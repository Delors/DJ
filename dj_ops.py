from typing import List, Set, Tuple
from sys import stderr
import os

from common import escape, open_file, InitializationFailed

from dj_ast import TDUnit, ASTNode, Body
from dj_ast import Operation, ComplexOperation


class Nop(Operation):

    def op_name() -> str: return "_"

    def process_entries(self, entries: List[str]) -> List[str]:
        return entries


NOP = Nop()


class Report(Operation):
    """The "report" operation prints out the entry. 

    A report generally terminates a sequence of operations, but it
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

    def __init__(self) -> None:
        super().__init__()

        self.reported_entries: Set[str] = set()
        """ The set of reported, i.e., printed, entries per entry. 
            This list is cleared by the `next_entry` method.
        """

    def op_name() -> str: return "report"

    def is_reporter(self) -> bool: return True

    def next_entry(self):
        if not self.td_unit.unique:
            self.reported_entries.clear()

    def do_print(self, entry: str):
        print(entry)

    def process_entries(self, entries: List[str]) -> List[str]:
        for e in entries:
            if e not in self.reported_entries:
                self.reported_entries.add(e)
                self.do_print(e)
        return entries


REPORT = Report()


class Write(Report):

    def op_name() -> str: return "write"

    def __init__(self, filename) -> None:
        super().__init__()
        self.filename = filename
        self.file = None

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        # let's append ... this makes it possible to have multiple 
        # write operations in a td file that output to the same 
        # target file
        self.file = open_file(self.filename, "a")

    def is_reporter(self) -> bool: return True

    def do_print(self, entry: str):
        print(entry, file=self.file)

    def close(self):
        try:
            self.file.close()
        except Exception as e:
            print(f"failed closing {self.filename}", file=stderr)
            pass

    def __str__(self):
        return f"{Write.op_name()} \"{escape(self.filename)}\""


class UseSet(Operation):

    def op_name() -> str: return "use"

    def __init__(self, setname) -> None:
        self.setname = setname

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if not isinstance(parent, ComplexOperation) or \
                not parent.ops[0] is self:  # TODO check that the complex operation is not a wrapped operation
            msg = f"{self}: a set use has to be a top level and the first operation."
            raise InitializationFailed(msg)

    def process_entries(self, entries: List[str]) -> List[str]:
        entries = self.td_unit.entry_sets[self.setname]
        if entries is None:
            return None
        else:
            return list(entries)

    def __str__(self):
        return f"{UseSet.op_name()} {self.setname}"


class StoreInSet(Operation):

    def op_name() -> str: return "store_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        self.setname = setname
        self.cop = cop

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, parent)

    def process_entries(self, entries: List[str]) -> List[str]:
        new_entries = self.cop.process_entries(entries)
        if self.td_unit.trace_ops:
            print(
                f"[trace] storing in {self.setname}: {new_entries}", file=stderr)
        if new_entries is not None:
            self.td_unit.entry_sets[self.setname].update(new_entries)
        return new_entries

    def close(self): self.cop.close()

    def __str__(self):
        return f"{{ {self.cop} }}> {self.setname}"


class StoreFilteredInSet(Operation):

    def op_name() -> str: return "store_filtered_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        self.setname = setname
        self.cop = cop

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, parent)

    def process_entries(self, entries: List[str]) -> List[str]:
        new_entries = self.cop.process_entries(entries)
        filtered_entries = set(entries)
        if new_entries is not None:
            filtered_entries.difference_update(new_entries)
            self.td_unit.entry_sets[self.setname].update(filtered_entries)
        if self.td_unit.trace_ops:
            print(
                f"[trace] storing in {self.setname}: {filtered_entries}", file=stderr)
        return new_entries

    def close(self): self.cop.close()

    def __str__(self):
        return f"{{ {self.cop} }}!> {self.setname}"


class StoreNotApplicableInSet(Operation):

    def op_name() -> str: return "store_not_applicable_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        self.setname = setname
        self.cop = cop

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, parent)

    def process_entries(self, entries: List[str]) -> List[str]:
        not_applicable = []
        new_entries = []
        for e in entries:
            r = self.cop.process_entries([e])
            if r is None:
                not_applicable.append(e)
            else:
                new_entries.extend(r)
        self.td_unit.entry_sets[self.setname].update(not_applicable)
        if self.td_unit.trace_ops:
            print(
                f"[trace] storing in {self.setname}: {not_applicable}", file=stderr)
        return new_entries

    def close(self): self.cop.close()

    def __str__(self):
        return f"{{ {self.cop} }}/> {self.setname}"


class MacroCall(Operation):
    """Represents a macro call."""

    def op_name() -> str: return "do"

    def __init__(self, macro_name: str):
        self.macro_name = macro_name
        self.cop: ComplexOperation = None

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop = td_unit.macros[self.macro_name]
        if self.cop is None:
            raise InitializationFailed(f"{self} unknown macro name")

    def next_entry(self):
        return self.cop.next_entry()

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

    def process_entries(self, entries: List[str]) -> List[str]:
        return self.cop.process_entries(entries)

    def close(self): self.cop.close()

    def __str__(self):
        return f"{MacroCall.op_name()} {self.macro_name}"


class KeepAlwaysModifier(Operation):
    """ Modifies the behavior of the wrapped transformer/extractor
        such that all input entries will also be output entries 
        additionally to those that are newly created by the 
        wrapped operation.
    """

    def op_name() -> str: return "+"

    def __init__(self, op: Operation):
        self.op = op

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        op = self.op
        op.init(td_unit, parent)
        if not op.is_transformer_or_extractor():
            raise InitializationFailed(
                f"{self}: {op} is no transformer or extractor")

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = []
        entries.append(entry)
        return entries

    def close(self):
        self.op.close()

    def __str__(self):
        return KeepAlwaysModifier.op_name() + str(self.op)


class KeepOnlyIfFilteredModifier(Operation):
    """ Modifies the behavior of the wrapped operation such that an
        input entry will be an output entry if the wrapped operation
        does not apply to the entry. I.e., if the wrapped operation 
        returns None, the entry is passed on otherwise the result
        of the wrapped operation is passed on as is.
    """

    def op_name() -> str: return "*"

    def __init__(self, op: Operation):
        self.op = op

    def is_transformer_or_extractor(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        op = self.op
        if not (op.is_transformer() or op.is_extractor()):
            raise InitializationFailed(
                f"{self}: op is no transformer or extractor")
        op.init(td_unit, parent)

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = [entry]
        return entries

    def close(self):
        self.op.close()

    def __str__(self):
        return KeepOnlyIfFilteredModifier.op_name() + str(self.op)


class NegateFilterModifier(Operation):
    """ Modifies the behavior of the wrapped filter such that if the 
        given entry is returned by the underlying filter, an empty 
        list will be returned and vice versa.
    """

    def op_name() -> str: return "!"

    def __init__(self, op: Operation):
        self.op = op

    def is_filter(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        op = self.op
        if not (op.is_filter()):
            raise InitializationFailed(f"{self}: {op} is no filter")
        op.init(td_unit, parent)

    def process_entries(self, entries: List[str]) -> List[str]:
        # "ignored" entries are already filtered beforehand...
        accepted_entries = self.op.process_entries(entries)
        return [e for e in entries if e not in accepted_entries]

    def close(self):
        self.op.close()

    def __str__(self):
        return NegateFilterModifier.op_name() + str(self.op)


class Or(Operation):

    def op_name() -> str: return "or"

    def __init__(self, cops: List[ComplexOperation]) -> None:
        self.cops = cops  # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

    def is_filter(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        for cop in self.cops:
            cop.init(td_unit, self)
        for cop in self.cops:
            if not cop.is_filter():
                msg = f"{self} {cop} is no filter"
                raise InitializationFailed(msg)

    def next_entry(self):
        for cop in self.cops:
            cop.next_entry()

    def process_entries(self, entries: List[str]) -> List[str]:
        # "ignored" entries are already filtered beforehand...
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

    def __str__(self):
        cops = ", ".join(map(lambda x: str(x), self.cops))
        return Or.op_name() + "(" + cops + ")"


class NonEmpty(Operation):
    """ Accepts (a set of) entries if - after applying all operations -
        the resulting set of entries is not empty / not applicable.
    """

    def op_name() -> str: return "non_empty"

    def __init__(self, on_none: bool, on_empty: bool, cop: ComplexOperation) -> None:
        self.on_none = on_none
        self.on_empty = on_empty
        self.cop = cop

    def is_filter(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.cop.init(td_unit, self)
        if self.on_empty and self.on_none:
            msg = f"{self} useless configuration; at least one parameter has to be false"
            raise InitializationFailed(msg)
        return self

    def process_entries(self, entries: List[str]) -> List[str]:
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

    def next_entry(self):
        self.cop.next_entry()

    def close(self):
        self.cop.close()

    def __str__(self):
        return f"{NonEmpty.op_name()}(N/A={self.on_none}, []={self.on_empty}, {self.cop})"


class All(Operation):
    """ Accepts a set of entries if all entries generated by the given operation
        satisfy the filter. I.e., the original entries are accepted - not those
        which are the result of the generator operation.
    """

    def op_name() -> str: return "all"

    def __init__(self, on_none: bool, on_empty: bool, cop: ComplexOperation, test: ComplexOperation) -> None:
        self.on_none = on_none
        self.on_empty = on_empty
        self.cop = cop
        self.test = test  # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

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

    def process_entries(self, entries: List[str]) -> List[str]:
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

    def next_entry(self):
        self.cop.next_entry()
        self.test.next_entry()

    def close(self):
        self.cop.close()
        self.test.close()

    def __str__(self):
        return f"{All.op_name()}(N/A={self.on_none}, []={self.on_empty}, {self.cop}, {self.test})"


class BreakUp(Operation):
    """ Takes a set of entries and breaks up each entry according to its filter.
    """

    def op_name() -> str: return "break_up"

    def __init__(self, test: ComplexOperation) -> None:
        self.test = test  # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

    def is_extractor(self) -> bool:
        return True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)

        self.test.init(td_unit, self)
        if not self.test.is_filter():
            msg = f"{self} {self.test} is not a filter"
            raise InitializationFailed(msg)

        return self

    def match_next(self, entry) -> List[Tuple[str, str]]:
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
            in unexpected results as shwon in the next example:
            
            `break_up(is_regular_word)` of `rumbleinthejungle` will
            result in:
            ```
            rumble
            he
            jungle
            int
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

    def process(self, entry: str) -> List[str]:
        solutions = []
        self.break_up(entry, [], solutions)
        if len(solutions) > 0:
            solutions.sort(key=lambda l: len(l))
            return solutions[0]
        else:
            return None

    def next_entry(self):
        self.test.next_entry()

    def close(self):
        self.test.close()

    def __str__(self):
        return f"{BreakUp.op_name()}({self.test})"
