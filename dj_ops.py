from abc import ABC, abstractmethod
from sys import stderr
from typing import final

from common import escape, open_file, InitializationFailed

from dj_ast import TDUnit, ASTNode
from dj_ast import Operation, ComplexOperation
from dj_ast import Transformer, Extractor, Filter


class Nop(Operation):

    def op_name() -> str: return "_"

    def is_reporter(self) -> bool: return True

    def process_entries(self, entries: list[str]) -> list[str]:
        return entries


NOP = Nop()


class ProcessEntriesHandler(ABC):
    """ Mixin Class which provides a basic implementation of 
        ` process_entries`. Intended to be used by operations
        that do not (need to) reason about the intermediate list of 
        entries as a whole but instead can reason about each entry on 
        its own.

        This class takes care of removing ignored entries.
        Duplicates are not removed; if required use the `ilist_unique` 
        operation afterwards.
    """

    @final
    def process_entries(self, entries: list[str]) -> list[str]:
        # PRE ISET_FOREACH IMPLEMENTATION!!!
        # td_unit = self.td_unit
        # all_none = True
        # all_new_entries_set = set()
        # all_new_entries_count = 0
        # all_new_entries = []
        # for entry in entries:
        #    new_entries = self.process(entry)
        #    if new_entries is not None:
        #        all_none = False
        #        for new_entry in new_entries:
        #            if not new_entry in td_unit.ignored_entries and len(new_entry) > 0:
        #                all_new_entries_set.add(new_entry)
        #                if len(all_new_entries_set) > all_new_entries_count:
        #                    all_new_entries_count += 1
        #                    all_new_entries.append(new_entry)
        # if all_none:
        #    return None
        # else:
        #    return all_new_entries
        # ______________________________________________________________
        # WITH DUPLICATE REMOVAL AND "FOR_ALL" SEMANTICS
        # td_unit = self.td_unit
        # all_new_entries_set = set()
        # all_new_entries_count = 0
        # all_new_entries = []
        # for entry in entries:
        #     new_entries = self.process(entry)
        #     if new_entries is not None:
        #         for new_entry in new_entries:
        #             if not new_entry in td_unit.ignored_entries and len(new_entry) > 0:
        #                 all_new_entries_set.add(new_entry)
        #                 if len(all_new_entries_set) > all_new_entries_count:
        #                     all_new_entries_count += 1
        #                     all_new_entries.append(new_entry)
        #     else:
        #         return None
        #
        # return all_new_entries

        ignored_entries = self.td_unit.ignored_entries
        all_none = True
        all_new_entries = []
        for entry in entries:
            new_entries = self.process(entry)
            if new_entries is not None:
                all_none = False
                for new_e in new_entries:
                    if not new_e in ignored_entries:
                        if len(new_e) > 0:
                            all_new_entries.append(new_e)
                    elif self.td_unit.trace_ops:
                        print(f"[trace] ignored derived entry: {new_e}")
        if all_none:
            return None
        else:
            return all_new_entries

    @abstractmethod
    def process(self, entry: str) -> list[str]:
        """
        Processes the given entry and returns the list of new entries.
        If an operation applies, i.e. the operation has some effect, 
        a list of new entries (possibly empty) will be returned.
        If an operation does not apply at all, None should be returned.
        Each operation has to clearly define when it applies and when not.

        For example, an operation to remove special chars would apply to
        an entry consisting only of special chars and would return
        the empty list in that case. If, however, the entry does not 
        contain any special characters, None would be returned.

        E.g., an operation that just extracts certain characters or which 
        replaces certain characters will always either return a 
        non-empty list (`[...]`) or `None` (didn't apply).

        A filter will either return [entry] or []. 
        """
        msg = "this method is called by process_entries and needs to be overwritten"
        raise NotImplementedError(msg)


class PerEntryTransformer(ProcessEntriesHandler, Transformer):
    pass


class PerEntryExtractor(ProcessEntriesHandler, Extractor):
    pass


class PerEntryFilter(ProcessEntriesHandler, Filter):
    pass


class Report(Operation):
    """The "report" operation prints out the entry. 

    A report often ends a sequence of operations, but it
    can also be used if an intermediate result is actually a desired 
    output and we do not want to have multiple operations. For example:

    report ___remove\_ws capitalize report___

    In the above case, we first print out the (original) entry. After
    that white space is removed. This will also filter the set of 
    entries down to those which had white space in the first place 
    and then those entries will be capitalized. For example,
    given the two entries:

        TestTest
        Dies ist ein Test

    the output will be:

        TestTest            [output due to initial report]
        Dies ist ein Test   [output due to initial report]
        Diesisteintest      [after removing ws and capitalization]

    notably:

        Testtest
        DiesisteinTest

    will not be output.
    """

    def op_name() -> str: return "report"

    def __init__(self) -> None:
        super().__init__()
        self.reported_entries: set[str] = set()
        """ The set of reported, i.e., printed, entries;
            only used if unique is enforced.
        """

    @final
    def is_reporter(self) -> bool: return True

    def do_print(self, entry: str):
        print(entry)

    def process_entries(self, entries: list[str]) -> list[str]:
        for e in entries:
            if self.td_unit.unique:
                if e not in self.reported_entries:
                    self.reported_entries.add(e)
                    self.do_print(e)
            else:
                self.do_print(e)
        return entries


REPORT = Report()


class Write(Report):

    reported_entries: dict[str, set[str]] = {}

    def op_name() -> str: return "write"

    def __init__(self, filename) -> None:
        super().__init__()
        self.filename = filename
        self.file = None

    def __str__(self):
        return f"{Write.op_name()} \"{escape(self.filename)}\""

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        # let's append ... this makes it possible to have multiple
        # write operations in a td file that output to the same
        # target file
        self.file = open_file(self.filename, "a")
        # We need one shared reported entries set per target to remove
        # duplicates (per effective output target) if specified!
        shared_reported_entries = Write.reported_entries.get(self.filename)
        if shared_reported_entries is not None:
            self.reported_entries = shared_reported_entries
        else:
            reported_entries = set()
            Write.reported_entries[self.filename] = reported_entries
            self.reported_entries = reported_entries
        return self

    def do_print(self, entry: str):
        print(entry, file=self.file)

    def close(self):
        try:
            self.file.close()
        except Exception as e:
            print(f"failed closing {self.filename}", file=stderr)
            pass


class Classify(Report):

    reported_entries: dict[str, set[str]] = {}

    def op_name() -> str: return "classify"

    def __init__(self, classifier) -> None:
        super().__init__()
        self.classifier = classifier

    def __str__(self):
        return f"{Classify.op_name()} \"{escape(self.classifier)}\""
    
    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        # We need one shared reported entries set per target to remove
        # duplicates (per effective output target) if specified!
        shared_reported_entries = Classify.reported_entries.get(self.classifier)
        if shared_reported_entries is not None:
            self.reported_entries = shared_reported_entries
        else:
            reported_entries = set()
            Classify.reported_entries[self.classifier] = reported_entries
            self.reported_entries = reported_entries
        return self

    def do_print(self, entry: str):
        print(f"{self.classifier}{entry}")


class UseSet(Operation):
    """
    Replaces the current dictionary entry with the entries from
    the specified sets. The list passed on to the next operation
    consists of the elements of the first set followed by the elements
    of all subsequent sets. However, the list may contain duplicates
    to enable, e.g., concat operations and statistics.
    """

    def op_name() -> str: return "use"

    def __init__(self, set_names) -> None:
        self.set_names = set_names

    def __str__(self):
        return f'{UseSet.op_name()} {" ".join(self.set_names)}'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if not isinstance(parent, ComplexOperation) or \
                not parent.ops[0] is self:  # TODO check that the complex operation is not a wrapped operation
            msg = f"{self}: a set use has to be a top level and the first operation."
            raise InitializationFailed(msg)
        for set_name in self.set_names:
            if td_unit.entry_sets.get(set_name) is None:
                msg = f"{self}: set name {set_name} is not defined"
                raise InitializationFailed(msg)
        return self

    def process_entries(self, _entries: list[str]) -> list[str]:
        if len(self.set_names) == 1:
            entries = self.td_unit.entry_sets[self.set_names[0]]
        else:
            entries = None
            for s in self.set_names:
                next_entries = self.td_unit.entry_sets[s]
                if next_entries is not None:
                    if entries is None:
                        entries = list(next_entries)
                    else:
                        entries.extend(next_entries)

        return entries


class AbstractStoreInSet(Operation):

    def __init__(self, setname, cop: ComplexOperation) -> None:
        self.setname = setname
        self.cop = cop

    @property
    @abstractmethod
    def operator(self) -> str: raise NotImplementedError()

    def __str__(self):
        return f"{{ {self.cop} }}{self.operator()} {self.setname}"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, parent)
        return self

    def next_entry(self):
        self.cop.next_entry()

    def close(self):
        self.cop.close()


class StoreInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        super().__init__(setname, cop)

    def operator(self) -> str: return ">"

    def process_entries(self, entries: list[str]) -> list[str]:
        new_entries = self.cop.process_entries(entries)
        if self.td_unit.trace_ops:
            print(
                f"[trace] storing in {self.setname}: {new_entries}", file=stderr)
        if new_entries is not None:
            self.td_unit.entry_sets[self.setname].extend(new_entries)
        return new_entries


class StoreFilteredInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_filtered_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        super().__init__(setname, cop)
        self.warning_shown = False

    def operator(self) -> str: return "[]>"

    def process_entries(self, entries: list[str]) -> list[str]:
        # Old, non-order preserving implementation:
        # new_entries = self.cop.process_entries(entries)
        # filtered_entries = set(entries)
        # if new_entries is not None:
        #    filtered_entries.difference_update(new_entries)
        #    self.td_unit.entry_sets[self.setname].extend(filtered_entries)
        #    if self.td_unit.trace_ops:
        #        msg = f"[trace] storing filtered in {self.setname}: {filtered_entries} => {self.td_unit.entry_sets[self.setname]}"
        #        print(msg, file=stderr)
        # elif self.td_unit.warn and not self.warning_shown:
        #    self.warning_shown = True
        #    msg = f"[warn] the result of {self.cop} returned an empty result because the operation was not applicable; did you wanted to use the '{{ <operation> }}/> <SET>' operation?"
        #    print(msg, file=stderr)
        # return new_entries
        filtered_entries = []
        all_new_entries = []
        for e in entries:
            new_entries = self.cop.process_entries([e])
            if new_entries is not None:
                if len(new_entries) == 0:
                    filtered_entries.append(e)
                else:
                    all_new_entries.extend(new_entries)
            elif self.td_unit.warn and not self.warning_shown:
                self.warning_shown = True
                msg = f"[warn] {self.cop}({e}) was not applicable; did you want to use: '{{ <operation> }}/> {self.setname}'?"
                print(msg, file=stderr)

        if len(filtered_entries) > 0:
            self.td_unit.entry_sets[self.setname].extend(filtered_entries)

        if self.td_unit.trace_ops:
            msg = f"[trace] storing filtered in {self.setname}: {filtered_entries} => {self.td_unit.entry_sets[self.setname]}"
            print(msg, file=stderr)

        return all_new_entries


class StoreNotApplicableInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_not_applicable_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        super().__init__(setname, cop)

    def operator(self) -> str: return "/>"

    def process_entries(self, entries: list[str]) -> list[str]:
        not_applicable = []
        new_entries = []
        for e in entries:
            r = self.cop.process_entries([e])
            if r is None:
                not_applicable.append(e)
            else:
                new_entries.extend(r)
        if self.td_unit.trace_ops:
            msg = f"[trace] storing not applicable in {self.setname}: {not_applicable}"
            print(msg, file=stderr)
        self.td_unit.entry_sets[self.setname].extend(not_applicable)
        return new_entries


class StoreFilteredAndNotApplicableInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_filtered_and_not_applicable_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        super().__init__(setname, cop)

    def operator(self) -> str: return "/[]>"

    def process_entries(self, entries: list[str]) -> list[str]:
        rejected = []
        new_entries = []
        for e in entries:
            r = self.cop.process_entries([e])
            if r is None or len(r) == 0:
                rejected.append(e)
            else:
                new_entries.extend(r)
        if self.td_unit.trace_ops:
            msg = f"[trace] storing filtered or not applicable in {self.setname}: {rejected}"
            print(msg, file=stderr)
        self.td_unit.entry_sets[self.setname].extend(rejected)
        return new_entries


class MacroCall(Operation):
    """Represents a macro call."""

    def op_name() -> str: return "do"

    def __init__(self, macro_name: str):
        self.macro_name = macro_name
        self.cop: ComplexOperation = None

    def __str__(self):
        return f"{MacroCall.op_name()} {self.macro_name}"

    def is_macro(self) -> bool:
        return True

    def is_transformer(self) -> bool:
        return self.cop.is_transformer()

    def is_extractor(self) -> bool:
        return self.cop.is_extractor()

    def is_transformer_or_extractor(self) -> bool:
        return self.cop.is_transformer_or_extractor()

    def is_filter(self) -> bool:
        return self.cop.is_filter()

    def is_reporter(self) -> bool:
        return self.cop.is_reporter()

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop = td_unit.macros[self.macro_name]
        if self.cop is None:
            raise InitializationFailed(f"{self} unknown macro name")
        return self

    def next_entry(self):
        return self.cop.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        return self.cop.process_entries(entries)

    def close(self):
        # "close" is called by the MacroDefinition class to ensure that
        # close is called only once per operation.
        pass


class AbstractTransformerOrExtractorModifier(Operation):

    def __init__(self, op: Operation) -> None:
        super().__init__()
        self.op = op

    def is_transformer(self) -> bool:
        return self.op.is_transformer()

    def is_extractor(self) -> bool:
        return self.op.is_extractor()

    @final
    def is_meta_op(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        op = self.op
        op.init(td_unit, parent)
        if not op.is_transformer_or_extractor():
            raise InitializationFailed(
                f"{self}: {op} is no transformer or extractor")
        return self

    def next_entry(self):
        self.op.next_entry()

    def close(self):
        self.op.close()


class KeepAlwaysModifier(AbstractTransformerOrExtractorModifier):
    """ Modifies the behavior of the wrapped transformer/extractor
        such that all input entries will also be output entries 
        additionally to those that are newly created by the 
        wrapped operation.
    """

    def op_name() -> str: return "+"

    def __init__(self, op: Operation):
        super().__init__(op)

    def __str__(self):
        return KeepAlwaysModifier.op_name() + str(self.op)

    def process_entries(self, entries: list[str]) -> list[str]:
        # The following variant passes on all elements in one
        # block. Hence, if a single entry is not applicable
        # the entire set is considered as being not applicable.
        # This semantics has proven to be unexpected and therefore
        # the behavior of this modifier is to process each
        # entry after another!
        # new_entries = self.op.process_entries(entries)
        # if new_entries is None or len(new_entries) == 0:
        #    return entries
        #
        # for e in entries:
        #    if not e in new_entries:
        #        new_entries.insert(0, e)
        #
        # return new_entries
        all_new_entries = []
        for e in entries:
            new_entries = self.op.process_entries([e])
            if new_entries is None:
                all_new_entries.append(e)
            else:
                if e not in new_entries:
                    all_new_entries.append(e)
                all_new_entries.extend(new_entries)
        return all_new_entries


class KeepOnlyIfNotApplicableModifier(AbstractTransformerOrExtractorModifier):
    """ Modifies the behavior of the wrapped operation such that an
        input entry will be an output entry if the wrapped operation
        does not apply to the entry. I.e., if the wrapped operation 
        returns None, the entry is passed on otherwise the result
        of the wrapped operation is passed on as is.
    """

    def op_name() -> str: return "*"

    def __init__(self, op: Operation):
        super().__init__(op)

    def __str__(self):
        return KeepOnlyIfNotApplicableModifier.op_name() + str(self.op)

    def process_entries(self, entries: list[str]) -> list[str]:
        """
        Processes the entries one after another and then considers
        the effect of the operation. 

        The alternative semantics where we always reason about
        the set as a whole has proven to be unexpected in practice!
        """
        op = self.op
        all_new_entries = []
        for e in entries:
            new_entries = op.process_entries([e])
            if new_entries is None:
                all_new_entries.append(e)
            else:
                if len(all_new_entries) == 0:
                    all_new_entries = new_entries
                else:
                    all_new_entries.extend(new_entries)
        return all_new_entries


class KeepIfRejectedModifier(AbstractTransformerOrExtractorModifier):
    """ Modifies the behavior of the wrapped operation such that an
        input entry will be an output entry if the wrapped operation
        does not apply or returns the empty set.
    """

    def op_name() -> str: return "~"

    def __init__(self, op: Operation):
        super().__init__(op)

    def __str__(self):
        return KeepIfRejectedModifier.op_name() + str(self.op)

    def process_entries(self, entries: list[str]) -> list[str]:
        op = self.op
        all_new_entries = []
        for e in entries:
            new_entries = op.process_entries([e])
            if new_entries is None or len(new_entries) == 0:
                all_new_entries.append(e)
            else:
                if len(all_new_entries) == 0:
                    all_new_entries = new_entries
                else:
                    all_new_entries.extend(new_entries)
        return all_new_entries


class NegateFilterModifier(Operation):
    """ Modifies the behavior of the wrapped filter such that if the 
        given entry is returned by the underlying filter, an empty 
        list will be returned and vice versa.
    """

    def op_name() -> str: return "!"

    def __init__(self, op: Operation):
        self.op = op

    def __str__(self):
        return NegateFilterModifier.op_name() + str(self.op)

    def is_filter(self) -> bool:
        return True

    def is_meta_op(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        op = self.op
        if not (op.is_filter()):
            raise InitializationFailed(f"{self}: {op} is no filter")
        op.init(td_unit, parent)
        return self

    def next_entry(self):
        self.op.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        # "ignored" entries are already filtered beforehand...
        accepted_entries = self.op.process_entries(entries)
        return [e for e in entries if e not in accepted_entries]

    def close(self):
        self.op.close()


class Or(Operation):

    def op_name() -> str: return "or"

    def __init__(self, cops: list[ComplexOperation]) -> None:
        self.cops = cops  # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

    def __str__(self):
        cops = ", ".join(map(lambda x: str(x), self.cops))
        return Or.op_name() + "(" + cops + ")"

    def is_filter(self) -> bool:
        return True

    def is_meta_op(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        for cop in self.cops:
            cop.init(td_unit, self)
        for cop in self.cops:
            if not cop.is_filter():
                msg = f"{self}: {cop} is no filter"
                raise InitializationFailed(msg)
        return self

    def next_entry(self):
        for cop in self.cops:
            cop.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        # "ignored" and empty entries are already filtered beforehand...
        new_entries = []
        for e in entries:
            for cop in self.cops:
                r = cop.process_entries([e])
                if len(r) != 0:
                    new_entries.append(e)
                    break
        return new_entries

    def close(self):
        for cop in self.cops:
            cop.close()


class IListIfAny(Operation):
    """ Accepts (a set of) intermediate entries if - after applying all operations -
        the resulting set of entries is not empty. I.e., the operation was
        applicable to at least one entry. In this case "applicable" is
        configurable.
    """

    def op_name() -> str: return "ilist_if_any"

    def __init__(self, on_none: bool, on_empty: bool, cop: ComplexOperation) -> None:
        self.on_none = on_none
        self.on_empty = on_empty
        self.cop = cop

    def __str__(self):
        config = ""
        if self.on_none or self.on_empty:
            config = f"N/A={self.on_none}, []={self.on_empty}, "
        return f"{IListIfAny.op_name()}({config}{self.cop})"

    def is_filter(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, self)
        if self.on_empty and self.on_none:
            msg = f"{self} useless configuration; at least one parameter has to be false"
            raise InitializationFailed(msg)
        return self

    def next_entry(self):
        self.cop.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        # "ignored" entries are already filtered beforehand...
        generated_entries = self.cop.process_entries(entries)
        if generated_entries is None:
            if self.on_none:
                return entries
            else:
                return []
        elif len(generated_entries) == 0:
            # The operation was applicable, but we have no "new" entries
            if self.on_empty:
                return entries
            else:
                return []
        else:
            return entries

    def close(self):
        self.cop.close()


class IListIfAll(Operation):
    """ Accepts a set of entries if all entries generated by the given 
        operation satisfy the filter. I.e., the original entries are 
        accepted - not those which are the result of the generator 
        operation.
    """

    def op_name() -> str: return "ilist_if_all"

    def __init__(self, on_none: bool, on_empty: bool, cop: ComplexOperation, test: ComplexOperation) -> None:
        self.on_none = on_none
        self.on_empty = on_empty
        self.cop = cop
        self.test = test  # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

    def __str__(self):
        config = ""
        if self.on_none or self.on_empty:
            config = f"N/A={self.on_none}, []={self.on_empty}, "
        return f"{IListIfAll.op_name()}({config}{self.cop}, {self.test})"

    def is_filter(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, self)
        self.test.init(td_unit, self)

        if not self.test.is_filter():
            msg = f"{self} {self.test} is not a filter"
            raise InitializationFailed(msg)

        return self

    def next_entry(self):
        self.cop.next_entry()
        self.test.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        # "ignored" entries are already filtered beforehand...
        generated_entries = self.cop.process_entries(entries)
        if generated_entries is None:
            if self.on_none:
                return entries
            else:
                return []
        elif len(generated_entries) == 0:
            # The operation was applicable, but we have no "new" entries
            if self.on_empty:
                return entries
            else:
                return []

        tested_entries = set(self.test.process_entries(generated_entries))
        if all(map(lambda e: True if e in tested_entries else False, generated_entries)):
            return entries
        else:
            return []

    def close(self):
        self.cop.close()
        self.test.close()


class IListForeach(Operation):
    """ Continues processing each entry of an intermediate set on its own.
    """

    def op_name() -> str: return "ilist_foreach"

    def __init__(self, cop: ComplexOperation) -> None:
        self.cop = cop

    def __str__(self):
        return f"{IListForeach.op_name()}({self.cop})"

    def is_extractor(self) -> bool:
        return self.cop.is_extractor()

    def is_transformer(self) -> bool:
        return self.cop.is_transformer()

    def is_filter(self) -> bool:
        return self.cop.is_filter()

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, self)
        return self

    def next_entry(self):
        self.cop.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        all_new_entries = None
        for e in entries:
            new_entries = self.cop.process_entries([e])
            if new_entries is not None:
                if all_new_entries is None:
                    all_new_entries = new_entries
                else:
                    all_new_entries.extend(new_entries)

        return all_new_entries

    def close(self):
        self.cop.close()


class BreakUp(PerEntryExtractor):
    """ Takes a entry and breaks up each entry according to its filter.
    """

    def op_name() -> str: return "break_up"

    def __init__(self, test: ComplexOperation) -> None:
        self.test = test  # ONLY FILTERS ARE ALLOWED (VALIDATED IN init)

    def __str__(self):
        return f"{BreakUp.op_name()}({self.test})"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.test.init(td_unit, self)

        if not self.test.is_filter():
            msg = f"{self} {self.test} is not a filter"
            raise InitializationFailed(msg)

        return self

    def next_entry(self):
        self.test.next_entry()

    def match_next(self, entry) -> list[tuple[str, str]]:
        """
            Returns potential matches.
            (Currently, the longest and second-longest match.)
            Returns the list of pairs:
                (<match>,<remaining>)

            A naive single longest matching break-up could lead to words
            that accidentally capture the first character of the next word. E.g.,
                ilovesun => accidental capturing of the s as part of loves results
                            in "i loves u n"; which is most likely not the
                            expected result!

            The longest possible match is always returned first!
        """
        len_entry = len(entry)

        if len_entry == 0:
            return None

        for i in range(0, len_entry):
            longest_part = entry[0:len_entry-i]
            if len(self.test.process_entries([longest_part])) > 0:
                result = [(longest_part, entry[len_entry-i:len_entry])]
                if len_entry-i > 1:
                    shorter_part = entry[0:len_entry-i-1]
                    if len(self.test.process_entries([shorter_part])) > 0:
                        result.append((shorter_part, entry[len_entry-i-1:]))
                return result

        return None

    def break_up(self,
                 text: str,
                 current_parts: list[str],
                 all_break_ups: list[list[str]]):
        """ Breaking-up an entry is generally not decidable and 
            multiple break-ups are possible. In particular in English
            and some other languages with single letter words (e.g.,
            I and a in English). Hence, we try multiple break-ups
            and chose one that leads to the fewest fragments.
            If we find a break-up in one or two fragments, we stop
            immediately. However, even this approach may result
            in unexpected results as shown in the next example:

            `break_up(is_regular_word)` of `rumbleinthejungle` will
            result in:
            ```
            rumble
            int
            he
            jungle            
            ``` 
            and not in the expected result:
            ```
            rumble
            in 
            the
            jungle
            ```
        """
        solutions = self.match_next(text)
        if solutions:
            for (part, remaining) in solutions:
                new_parts = current_parts.copy()
                new_parts.append(part)
                if len(remaining) == 0:
                    all_break_ups.append(new_parts)
                    # recall that the possible longest match is
                    # returned first - hence, a complete match is
                    # always preferred.
                    break
                else:
                    self.break_up(remaining, new_parts, all_break_ups)

    def process(self, entry: str) -> list[str]:
        solutions = []
        self.break_up(entry, [], solutions)
        if len(solutions) > 0:
            solutions.sort(key=lambda l: len(l))
            return solutions[0]
        else:
            return None

    def close(self):
        self.test.close()
