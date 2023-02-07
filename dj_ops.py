from typing import List
from sys import stderr

from common import escape, enrich_filename, InitializationFailed

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
        self.reported_entries.clear()
        return super().next_entry()

    def do_print(self, entry: str):
        print(entry)

    def process(self, entry: str) -> List[str]:
        if entry not in self.reported_entries:
            self.reported_entries.add(entry)
            self.do_print(entry)

        return [entry]


REPORT = Report()


class Write(Report):

    def op_name() -> str: return "write"

    def __init__(self, filename) -> None:
        super().__init__()
        self.filename = filename
        self.file = None

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        # let's append ... this enables multiple writes to the same file
        self.file = open(enrich_filename(self.filename), "a", encoding="utf-8")

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

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        if not isinstance(parent, ComplexOperation) or \
                not parent.ops[0] is self:  # TODO check that the complex operation is not a wrapped operation
            msg = f"a set use has to be a top level and the first operation."
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

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        self.cop.init(td_unit, parent, verbose)

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
        # return f"{StoreInSet.op_name()} {self.setname}({self.cop})"
        return f"{{ {self.cop} }}> {self.setname}"


class StoreFilteredInSet(Operation):

    def op_name() -> str: return "store_filtered_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        self.setname = setname
        self.cop = cop

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        self.cop.init(td_unit, parent, verbose)

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
        # return f"{StoreFilteredInSet.op_name()} {self.setname}({self.cop})"
        return f"{{ {self.cop} }}!> {self.setname}"


class StoreNotApplicableInSet(Operation):

    def op_name() -> str: return "store_not_applicable_in"

    def __init__(self, setname, cop: ComplexOperation) -> None:
        self.setname = setname
        self.cop = cop

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        self.cop.init(td_unit, parent, verbose)

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
        # return f"{StoreFilteredInSet.op_name()} {self.setname}({self.cop})"
        return f"{{ {self.cop} }}/> {self.setname}"

class MacroCall(Operation):
    """Represents a macro call."""

    def op_name() -> str: return "do"

    def __init__(self, macro_name: str):
        self.macro_name = macro_name
        self.cop: ComplexOperation = None

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        self.cop = td_unit.macros[self.macro_name]

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

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        op = self.op
        op.init(td_unit, parent, verbose)
        if not op.is_transformer_or_extractor():
            raise InitializationFailed(
                f"[{self}] no transformer or extractor: {op}")

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

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        op = self.op
        if not (op.is_transformer() or op.is_extractor()):
            raise InitializationFailed(
                f"[{self} no transformer or extractor: {op}")
        op.init(td_unit, parent, verbose)

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

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        op = self.op
        if not (op.is_filter()):
            raise InitializationFailed(f"[{self}] no filter: {op}")
        op.init(td_unit, parent, verbose)

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries == []:
            return [entry]
        else:
            return []

    def close(self):
        self.op.close()

    def __str__(self):
        return NegateFilterModifier.op_name() + str(self.op)


class Or(Operation):

    def op_name() -> str: return "or"

    def __init__(self, cops: List[ComplexOperation]) -> None:
        self.cops = cops # ONLY FILTERS ARE ALLOWED HERE (VALIDATED IN init)

    def is_filter(self) -> bool:
        return True

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        for cop in self.cops:
            if not cop.is_filter():
                msg = f"[{self}] no filter: {cop}"
                raise InitializationFailed(msg)
        for cop in self.cops:
            cop.init(td_unit, parent, verbose)

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
