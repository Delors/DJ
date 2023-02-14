from abc import ABC, abstractmethod
from typing import List, Tuple
from importlib import import_module
from sys import stderr, exit
import traceback

from common import InitializationFailed, read_utf8file


class ASTNode(ABC):

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        """ Performs a semantic validation and initialization 
            of this node and then calls the method on child nodes. 

            In case of an error an InitializationFailed exception is raised. 
            An example of a semantic validation is to check
            if a child node of a logical not operator ("!") is a 
            filter node.

            Validate only checks for conceptual errors. 
        """
        self.td_unit = td_unit
        self.parent = parent
        self.verbose = verbose


class Comment(ASTNode):

    def __init__(self, comment):
        self.comment = comment

    def __str__(self):
        return self.comment


class Operation(ASTNode):
    """ Representation of an operation. An operation processes one to many 
        entries and produces zero (`[]`) to many entries. An operation which 
        does not apply to an entry/a set of entries returns `None`. 
        For a precise definition of "does not apply" see the documentation 
        of the respective classes of operations.

        An operation is either:
        - a transformation which takes an entry and returns None or between
            zero and many new entries; i.e., the original entry will
            never be returned. If a transformation does not generate
            new entries, the transformation is considered to be not
            applicable to the entry and None is returned.
            For example, if an entry only consists of special characters
            and the operation removes all special characters, a empty 
            list (not None) will be returned. But, if the entry contains
            no special characters and, therefore, nothing would be removed
            None would be returned.
        - an extractor which extracts one to multiple parts of an entry. 
            An extractor might "extract" the original entry. For example,
            an extractor for numbers might return the original entry if 
            the entry just consists of numbers.
            An extractor which does not extract a single entry is not
            considered to be applicable and None is returned. Hence,
            an extractor never returns an empty list.
        - a meta operation ("+","*","!") which manipulates the behavior 
            of a filter, an extractor or a transformation.
        - a filter operation which takes an entry and either returns
            the entry (`[entry]`) or the empty list (`[]`). Hence, a filter
            is considered to be always applicable.
        - a report operation which either collects some statistics or
            which prints out an entry but always just returns the entry
            as is.
        - a macro which combines one to many operations and which basically
            provides a convenience method to facilitate the definition of
            a set of operations which should be carried out in a specific order
            and which may be used multiple times.

        Lifecycle:
        During parsing an operation is created. After parsing has completed
        the initialization is performed in a second step ("init(...)"). After
        that each entry in a dictionary will be processed. Before a
        new entry is processed "new_entry()" is called to inform the 
        operation that a new dictionary entry will be processed.
        1. __init__ (should not throw errors/exception that may be related to user input)
        2. init (should validate the configuration/setup and throw InitializationFailedExceptions in case of configuration/setup issues!)
        3. <for each entry of a dictionary>:
            3.1 next_entry
            3.1 process_entries (which calls process_entry)
        5. close
    """

    @staticmethod
    @abstractmethod
    def op_name() -> str:
        """ The operation's name or mnemonic."""
        raise NotImplementedError("subclasses must override this method")

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)

    def next_entry(self):
        pass

    def process_entries(self, entries: List[str]) -> List[str]:
        """
        Processes each entry of the list and applies the respective operation.

        Returns a list (potentially empty) if the operation could be 
        applied to (at least) some entries. The entries in the given list need
        to be checked if they should be ignored. That is, 
        __Process entries is responsible for checking for entries which
        should be explicitly ignored and those which have length zero!__

        Returns None if the operation could not be applied. 

        """
        td_unit = self.td_unit
        all_none = True
        all_new_entries = set()
        for entry in entries:
            new_entries = self.process(entry)
            if new_entries is not None:
                all_none = False
                for new_entry in new_entries:
                    if not new_entry in td_unit.ignored_entries and len(new_entry) > 0:
                        all_new_entries.add(new_entry)
        if all_none:
            return None
        else:
            return list(all_new_entries)

    def process(self, entry: str) -> List[str]:
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
        pass

    def close(self):
        """
        Close is called after all entries of the dictionary have been
        processed and all operations have been executed.
        """
        pass

    def is_transformer(self) -> bool: return False

    def is_extractor(self) -> bool: return False

    def is_transformer_or_extractor(self) -> bool:
        return self.is_transformer() or self.is_extractor()

    def is_meta_op(self) -> bool: return False

    def is_macro(self) -> bool: return False

    def is_reporter(self) -> bool: return False

    def is_filter(self) -> bool: return False

    def __str__(self):
        return self.__class__.op_name()


class Transformer(Operation):
    def is_transformer(self) -> bool: return True


class Filter(Operation):
    def is_filter(self) -> bool: return True


class Extractor(Operation):
    def is_extractor(self) -> bool: return True


class ComplexOperation(ASTNode):
    """ Representation of a sequence of operations.

        Instantiation of a complex operation which is made up of 
        multiple atomic/macro operations. An instance of ComplexOperation 
        basically just handles applying the atomic operations to 
        an entry and (potentially) every subsequently created entry.
    """

    def __init__(self, ops: List[Operation]):
        if not ops or len(ops) == 0:
            # The following exception is related to a programming
            # error, because the grammar enforces that a complex
            # operation is never empty. I.e., in that case a
            # syntax error would be signaled and that one would need
            # to be handled by the user.
            raise ValueError(f"no operations: {ops}")
        self.ops = ops

    def __str__(self) -> str:
        return " ".join(map(str, self.ops))

    def is_filter(self) -> bool:
        return all(op.is_filter() for op in self.ops)

    def is_transformer(self) -> bool:
        return all(op.is_transformer() for op in self.ops)

    def is_extractor(self) -> bool:
        return all(op.is_extractor() for op in self.ops)

    def is_transformer_or_extractor(self) -> bool:
        return all(op.is_extractor() or op.is_transformer() for op in self.ops)

    def is_reporter(self) -> bool:
        return all(op.is_reporter() for op in self.ops)

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        for op in self.ops:
            op.init(td_unit, self, verbose)

    def next_entry(self):
        for op in self.ops:
            op.next_entry()

    def process_entries(self, entries):
        td_unit: TDUnit = self.td_unit
        previous_entries = None
        current_entries = entries
        for op in self.ops:
            if current_entries is None or len(current_entries) == 0:
                break
            try:
                previous_entries = current_entries
                current_entries = op.process_entries(current_entries)
                if td_unit.trace_ops:
                    s_op = str(op)
                    if s_op.startswith("use"):
                        print(
                            f"[trace] {s_op} => {current_entries}",
                            file=stderr)
                    else:
                        print(
                            f"[trace] {s_op} ( {previous_entries} ) => {current_entries}",
                            file=stderr)
            except Exception as e:
                print(traceback.format_exc(), file=stderr)
                print(f"[error] {op}({entries}) failed: {str(e)}", file=stderr)
                exit(-2)

        return current_entries

    def close(self):
        for op in self.ops:
            op.close()


class SetDefinition(ASTNode):
    """
    Represents a named set. A named set is initialized/reset before an
    entry of the dictionary is processed and holds (intermediate) 
    results created while processing the entry.
    """

    def __init__(self, name):
        self.name = name

    def __str__(self) -> str:
        return "set "+self.name

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        td_unit.entry_sets[self.name] = set()


class IgnoreEntries(ASTNode):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self) -> str:
        return "ignore \""+self.filename+"\""

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        # 1. reads in the file and stores the entries to
        #    be ignored in the TDUnit object.
        to_be_ignored = set(read_utf8file(self.filename))
        td_unit.ignored_entries = td_unit.ignored_entries.union(to_be_ignored)
        if verbose:
            msg = f"[debug] ignoring:{self.filename} (#{len(to_be_ignored)})"
            print(msg, file=stderr)


class ConfigureOperation(ASTNode):

    def __init__(self, module_name, field_name, field_value):
        self.module_name = module_name
        self.field_name = field_name
        self.field_value = field_value

    def __str__(self):
        return \
            "config " +\
            self.module_name+" " +\
            self.field_name+" " +\
            self.field_value

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        op_module = import_module("operations."+self.module_name)
        op_class_name = "".join(
            map(lambda x: x.capitalize(), self.module_name.split("_"))
        )
        op_class = getattr(op_module, op_class_name)
        value = None
        try:
            old_value = getattr(op_class, self.field_name)
        except AttributeError:
            msg = f"unknown field name: {op_class_name}.{self.field_name}"
            raise InitializationFailed(msg)

        if verbose:
            print(
                f"[debug] updating: " +
                f"{op_module.__name__}.{op_class.__name__}.{self.field_name} = " +
                f"{self.field_value} (old value: {old_value})", file=stderr)

        value_type = type(old_value)
        if value_type == int:
            value = int(self.field_value)
        elif value_type == bool:
            value = bool(self.field_value)
        elif value_type == float:
            value = float(self.field_value)
        elif value_type == str:
            value = self.field_value
        else:
            msg = f"unsupported: {value_type}; supported int, bool, float and str"
            raise InitializationFailed(msg)

        setattr(op_class, self.field_name, value)


class MacroDefinition(ASTNode):

    def __init__(self, name: str, cop: ComplexOperation):
        self.name = name
        self.cop = cop

    def __str__(self) -> str:
        return "def "+self.name+" "+str(self.cop)

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        # 1. reads in the file and stores the entries to
        #    be ignored in the TDUnit object.
        td_unit.macros[self.name] = self.cop
        self.cop.init(td_unit, self, verbose)

    def close(self):
        self.cop.close()


class Header(ASTNode):

    def __init__(self, setup_ops: List[ASTNode]):
        self.setup_ops = setup_ops

    def __str__(self):
        return "\n".join(str(o) for o in self.setup_ops)

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        for o in self.setup_ops:
            o.init(td_unit, self, verbose)

    def close(self):
        for setup_op in self.setup_ops:
            if isinstance(setup_op, MacroDefinition):
                setup_op.close()


class Body(ASTNode):

    def __init__(self, cops: List[ComplexOperation]):
        self.cops = cops
        # the initialization will be completed by "init"
        self.td_unit = None

    def __str__(self):
        return "\n".join(map(str, self.cops))

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        self.td_unit = td_unit
        for cop in self.cops:
            cop.init(td_unit, self, verbose)

    def process(self, entry: str):
        # -1. The ignored check for the entry is done by TDUnit

        # information all operations that a new entry will be processed
        for cop in self.cops:
            if not isinstance(cop, Comment):
                cop.next_entry()

        # apply all operations in the specified order on the entry
        for cop in self.cops:
            if not isinstance(cop, Comment):
                if self.td_unit.trace_ops:
                    escaped_entry = entry.replace(
                        "\\", "\\\\").replace("\"", "\\\"")
                    s_cop = str(cop)
                    if s_cop.startswith("use"):
                        print(
                            f'[trace] applying: {s_cop}',
                            file=stderr
                        )
                    else:
                        print(
                            f'[trace] applying: {s_cop}( {escaped_entry} )',
                            file=stderr
                        )
                cop.process_entries([entry])

    def close(self):
        for cop in self.cops:
            if not isinstance(cop, Comment):
                cop.close()


class TDUnit(ASTNode):

    def __init__(self, header: Header, body: Body):
        self.header = header
        self.body = body

        # The following fields will be fully initialized during
        # the explicit initialization step ("init").

        self.ignored_entries: set[str] = set()

        # A map from str (set name) to current entries.
        self.entry_sets: Tuple[str, set[str]] = {}

        self.macros = {}  # A map from str to complex operation objects

        self.report_progress = False  # report progress w.r.t. the processed entries

        self.trace_ops = False  # provide detailed information about an operation's effect

        self.verbose = False  # provide configuration and initialization related information

    def __str__(self):
        return str(self.header)+"\n\n"+str(self.body)

    def init(self, td_unit: 'TDUnit', parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        self.header.init(td_unit, self, verbose)
        self.body.init(td_unit, self, verbose)

    def process(self, no: int, entry: str):
        if entry not in self.ignored_entries:
            if self.report_progress:
                print(f"[progress] processing #{no}: {entry}", file=stderr)

            # clear all (intermediate) sets
            for k in self.entry_sets.keys():
                self.entry_sets[k].clear()
            # delegate to the body the application of the rules
            self.body.process(entry)

        else:
            if self.report_progress:
                print(f"[progress] ignoring   #{no}: {entry}", file=stderr)

    def close(self):
        self.header.close()
        self.body.close()
