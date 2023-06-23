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
        td_unit = self.td_unit
        ignored_entries = td_unit.ignored_entries
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
                    elif td_unit.trace_ops:
                        td_unit.trace(f"ignored derived entry: {new_e}")
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
    that white space is removed. This will also filter the list of 
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
        self.reported_entries: list[str] = list()
        """ The list of reported, i.e., printed, entries;
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
        shared_reported_entries = Classify.reported_entries.get(
            self.classifier)
        if shared_reported_entries is not None:
            self.reported_entries = shared_reported_entries
        else:
            reported_entries = set()
            Classify.reported_entries[self.classifier] = reported_entries
            self.reported_entries = reported_entries
        return self

    def do_print(self, entry: str):
        original_entry = ""
        if self.td_unit.restart_context and self.td_unit.print_original:
            original_entry = f'"{escape(self.td_unit.restart_context[0][0])}", '

        print(f"{original_entry}{self.classifier}{entry}")


class UseSet(Operation):
    """
    Replaces the current dictionary entry with the entries from
    the specified lists. The list passed on to the next operation
    consists of the elements of the first list followed by the elements
    of all subsequent lists. However, the list may contain duplicates
    to enable, e.g., concat operations and statistics.
    """

    def op_name() -> str: return "use"

    def __init__(self, list_names) -> None:
        self.list_names = list_names

    def __str__(self):
        return f'{UseSet.op_name()} {" ".join(self.list_names)}'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if not isinstance(parent, ComplexOperation) or \
                not parent.ops[0] is self:  # TODO check that the complex operation is not a wrapped operation
            msg = f"{self}: a list use has to be a top level and the first operation."
            raise InitializationFailed(msg)
        for list_name in self.list_names:
            if td_unit.entry_lists.get(list_name) is None:
                msg = f"{self}: list name {list_name} is not defined"
                raise InitializationFailed(msg)
        return self

    def process_entries(self, _entries: list[str]) -> list[str]:
        if len(self.list_names) == 1:
            entries = self.td_unit.entry_lists[self.list_names[0]]
        else:
            entries = None
            for s in self.list_names:
                next_entries = self.td_unit.entry_lists[s]
                if next_entries is not None:
                    if entries is None:
                        entries = list(next_entries)
                    else:
                        entries.extend(next_entries)

        return entries


class AbstractStoreInSet(Operation):

    def __init__(self, listname, cop: ComplexOperation) -> None:
        self.listname = listname
        self.cop = cop

    @property
    @abstractmethod
    def operator(self) -> str: raise NotImplementedError()

    def __str__(self):
        return f"{{ {self.cop} }}{self.operator()} {self.listname}"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, parent)
        if self.td_unit.entry_lists.get(self.listname) is None:
            msg = f"{self}: no list {self.listname} definition found"
            raise InitializationFailed(msg)
        return self

    def next_entry(self):
        self.cop.next_entry()

    def close(self):
        self.cop.close()


class StoreInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_in"

    def __init__(self, listname, cop: ComplexOperation) -> None:
        super().__init__(listname, cop)

    def operator(self) -> str: return ">"

    def process_entries(self, entries: list[str]) -> list[str]:
        td_unit = self.td_unit
        new_entries = self.cop.process_entries(entries)
        if td_unit.trace_ops:
            td_unit.trace(f"storing in {self.listname}: {new_entries}")
        if new_entries is not None:
            td_unit.entry_lists[self.listname].extend(new_entries)
        return new_entries


class StoreFilteredInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_filtered_in"

    def __init__(self, listname, cop: ComplexOperation) -> None:
        super().__init__(listname, cop)
        self.warning_shown = False

    def operator(self) -> str: return "[]>"

    def process_entries(self, entries: list[str]) -> list[str]:
        td_unit = self.td_unit
        filtered_entries = []
        all_new_entries = []
        for e in entries:
            new_entries = self.cop.process_entries([e])
            if new_entries is not None:
                if len(new_entries) == 0:
                    filtered_entries.append(e)
                else:
                    all_new_entries.extend(new_entries)
            elif td_unit.warn and not self.warning_shown:
                self.warning_shown = True
                msg = f"[warn] {self.cop}({e}) was not applicable; did you want to use: '{{ <operation> }}/> {self.listname}'?"
                print(msg, file=stderr)

        if len(filtered_entries) > 0:
            td_unit.entry_lists[self.listname].extend(filtered_entries)

        if self.td_unit.trace_ops:
            td_unit.trace(
                f"storing filtered in {self.listname}: {filtered_entries} => {td_unit.entry_lists[self.listname]}")

        return all_new_entries


class StoreNotApplicableInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_not_applicable_in"

    def __init__(self, listname, cop: ComplexOperation) -> None:
        super().__init__(listname, cop)

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
            msg = f"storing not applicable in {self.listname}: {not_applicable}"
            self.td_unit.trace(msg)
        self.td_unit.entry_lists[self.listname].extend(not_applicable)
        return new_entries


class StoreFilteredOrNotApplicableInSet(AbstractStoreInSet):

    def op_name() -> str: return "store_filtered_or_not_applicable_in"

    def __init__(self, listname, cop: ComplexOperation) -> None:
        super().__init__(listname, cop)

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
            msg = f"storing filtered or not applicable in {self.listname}: {rejected}"
            self.td_unit.trace(msg)
        self.td_unit.entry_lists[self.listname].extend(rejected)
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
        # the entire list is considered as being not applicable.
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
        the list as a whole has proven to be unexpected in practice!
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
        does not apply or returns the empty list.
        Recall that (in particular) a meta operation often takes the 
        shape of the wrapped complex operation and if that complex
        operation consists of filters and transformers/extractors then
        the entire complex operation is a transformer/extractor but
        may still return the empty list or None.
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


class Result(Operation):

    def op_name() -> str: return "restart"

    def process_entries(self, entries: list[str]) -> list[str]:
        restart_context = self.td_unit.restart_context
        if restart_context:
            restart_op: Restart = restart_context[-1]
            restart_op.results.extend(entries)
            if self.td_unit.trace_ops:
                self.td_unit.trace(f"results: {restart_op.results}")

            Restart.all_results.update(entries)

        return entries


RESULT = Result()


class Restart(Operation):
    """ Takes the entries and repeats all operations for each entry.
        - Keeps a list of all entries that were put in the restart list
          to avoid analyzing it over and over again.
        - Uses the list of results identified by the user using the 
          result operation, to prevent the processing of terms that 
          were already identified as a result and to return these
          elements as the result's operation.         
    """

    # This set is collaboratively maintained by Restart and Result
    # and contains all entries for which the operations will
    # be restarted as well as all results (for which no restart)
    # will be performed.
    all_results = set()

    def op_name() -> str: return "restart"

    def __init__(self, count: int, filter_cop: ComplexOperation, cop: ComplexOperation) -> None:
        self.count = count
        self.filter_cop = filter_cop
        self.cop = cop
        # The set of entries for which we restarted the computation
        # This set cannot be global, because different paths may
        # lead to the same entry, but only some paths are preferable.
        self.restarted_entries: set[str] = set()
        # The set of results (entries passed to "result") of this
        # restart operation
        self.results: list[str] = []

    def __str__(self):
        count = ""
        # The value "256" is a bit arbitrary, but we never expect any
        # meaningful dj script to except a restart opertion more than
        # 256 times....
        if self.count < 256:
            count = f" {self.count}"
        return f"{Restart.op_name()}{count}({self.filter_cop}, {self.cop})"

    def is_meta_op(self) -> bool:
        return True
    
    def is_transformer_or_extractor(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.filter_cop.init(td_unit, self)
        self.cop.init(td_unit, self)
        if not self.filter_cop.is_filter():
            msg = f"{self} the filter is not a filter operation"
            raise InitializationFailed(msg)
        return self

    def next_entry(self):
        self.filter_cop.next_entry()
        self.cop.next_entry()
        self.results.clear()
        self.restarted_entries.clear()
        Restart.all_results.clear()

    def process_entries(self, entries: list[str]) -> list[str]:
        # "ignored" entries are already filtered beforehand...

        td_unit = self.td_unit
        entry_lists = self.td_unit.entry_lists

        # check if we want to do (yet another) restart
        if td_unit.restart_context.count(self) >= self.count:
            return None

        filtered_entries = self.filter_cop.process_entries(entries)
        if len(filtered_entries) == 0:
            return []
        for fe in filtered_entries:
            if fe in Restart.all_results:
                continue

            restart_entries = self.cop.process_entries([fe])
            if not restart_entries:
                continue

            for re in restart_entries:
                if re in self.restarted_entries or re in Restart.all_results:
                    if td_unit.trace_ops:
                        td_unit.trace(
                            f"rejected restart (already processed): {re}")
                    continue
                self.restarted_entries.add(fe)
                self.restarted_entries.add(re)

                # 1. let's safe the current evaluation context;
                #    i.e., the values of the current lists and the
                #    current restart context.
                old_entry_lists = {}
                for (k, v) in entry_lists.items():
                    old_entry_lists[k] = v
                    entry_lists[k] = []
                td_unit.restart_context.append((fe, re))
                td_unit.restart_context.append(self)

                # 2. apply all operations to a fresh context
                #    (however, we have not called next_entry
                #    as this function is ONLY called for original
                #    entries read from stdin, a file or explicitly
                #    generated)
                td_unit.body.apply_cops(re)

                # 3. restore the evaluation context before we continue
                td_unit.restart_context.pop()
                td_unit.restart_context.pop()
                for (k, v) in old_entry_lists.items():
                    entry_lists[k] = v

                if td_unit.trace_ops:
                    td_unit.trace(
                        f"{self}({fe})({re}): {self.results}) finished")

        if len(self.results) == 0:
            return None
        else:
            processed_results = set()
            final_results = []
            for r in self.results:
                if r not in processed_results:
                    processed_results.add(r)
                    final_results.append(r)

            return final_results

    def close(self):
        self.filter_cop.close()
        self.cop.close()


class IListIfAny(Operation):
    """ Accepts (a list of) intermediate entries if - after applying all operations -
        the resulting list of entries is not empty. I.e., the operation was
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
    """ Accepts a list of entries if all entries generated by the given 
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

        tested_entries = list(self.test.process_entries(generated_entries))
        if all([True for g in generated_entries if g in tested_entries]):
        #if all(map(lambda e: True if e in tested_entries else False, generated_entries)):
            return entries
        else:
            return []

    def close(self):
        self.cop.close()
        self.test.close()

class IListIfElse(Operation):
    """ Performs a test and depending on the result either the
        "if" or the "else" operation is performed.
    """

    def op_name() -> str: return "ilist_if_else"

    def __init__(self, test: ComplexOperation, if_cop: ComplexOperation, else_cop: ComplexOperation) -> None:
        self.if_cop = if_cop
        self.else_cop = else_cop        
        self.test = test  # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

    def __str__(self):
        return f"{IListIfElse.op_name()}({self.test}, {self.if_cop}, {self.else_cop})"

    def is_meta_op(self) -> bool:
        return True

    def is_filter(self) -> bool:
        return self.if_cop.is_filter() and self.else_cop.is_filter()
    
    def is_extractor(self) -> bool:
        return self.if_cop.is_extractor() and self.else_cop.is_extractor()

    def is_transformer(self) -> bool:
        return self.if_cop.is_transformer() and self.else_cop.is_transformer()

    def is_transformer_or_extractor(self) -> bool:
        return self.if_cop.is_transformer_or_extractor() or \
            self.else_cop.is_transformer_or_extractor()


    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.if_cop.init(td_unit, self)
        self.else_cop.init(td_unit, self)
        self.test.init(td_unit, self)

        if not self.test.is_filter():
            msg = f"{self} {self.test} is not a filter"
            raise InitializationFailed(msg)

        return self

    def next_entry(self):
        self.if_cop.next_entry()
        self.else_cop.next_entry()
        self.test.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        # "ignored" entries are already filtered beforehand...
        if entries == self.test.process_entries(entries):
            return self.if_cop.process_entries(entries)
        else:
            return self.else_cop.process_entries(entries)

    def close(self):
        self.if_cop.close()
        self.else_cop.close()
        self.test.close()


class IListForeach(Operation):
    """ Continues processing each entry of an intermediate list on its own.
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


class IListRatio(Operation):
    """ Computes the ratio between the lists of elements or the sums
        of the lengths of the entries of both list.
    """

    def op_name() -> str: return "ilist_ratio"

    def __init__(self, joined: bool, op: str, ratio: float, before_cop: ComplexOperation, after_cop: ComplexOperation) -> None:
        self.joined = joined
        self.op = op
        self.ratio = ratio
        self.before_cop = before_cop
        self.after_cop = after_cop

    def __str__(self):
        params = ""
        if self.joined:
            params = "joined"
        params += " "+self.op+" "+str(self.ratio)
        return f"{IListRatio.op_name()} {params}({self.before_cop}, {self.after_cop})"

    def is_extractor(self) -> bool:
        return self.before_cop.is_extractor() or \
            self.after_cop.is_extractor()

    def is_transformer(self) -> bool:
        return self.before_cop.is_transformer() or \
            self.after_cop.is_transformer()
    
    def is_transformer_or_extractor(self) -> bool:
        return self.before_cop.is_transformer_or_extractor() or \
            self.after_cop.is_transformer_or_extractor()

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.before_cop.init(td_unit, self)
        self.after_cop.init(td_unit, self)
        if not self.after_cop.is_transformer_or_extractor():
            msg = f"{self}: the second operation is no transformer or extractor {self.after_cop} "
            raise InitializationFailed(msg)
        return self

    def next_entry(self):
        self.before_cop.next_entry()
        self.after_cop.next_entry()

    def process_entries(self, entries: list[str]) -> list[str]:
        before_entries = self.before_cop.process_entries(entries)
        if not before_entries:
            return None
        after_entries = self.after_cop.process_entries(before_entries)
        if not after_entries:
            return None
        
        if self.joined:
            before_count = sum([len(e) for e in before_entries])
            after_count = sum([len(e) for e in after_entries])
        else:
            before_count = len(before_entries)
            after_count = len(after_entries)

        current_ratio = before_count / after_count
            
        if (self.op == "<" and current_ratio >= self.ratio) or \
            (self.op == ">" and current_ratio <= self.ratio):
            return None
        
        return after_entries

    def close(self):
        self.before_cop.close()
        self.after_cop.close()


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
