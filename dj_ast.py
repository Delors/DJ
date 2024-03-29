from abc import ABC, abstractmethod, abstractstaticmethod
from typing import Iterable, final
from importlib import import_module
from itertools import chain
from sys import stderr, exit
import traceback

from common import InitializationFailed, read_utf8file, escape, open_file


class ASTNode(ABC):

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode'):
        """ Performs semantic validation and initialization 
            of this node and then calls the method on child nodes. 

            I.e., the class' __init__ method is not expected to
            raise any exceptions/errors; this should always be done
            by this method.

            In case of an error an InitializationFailed exception has 
            to be raised. 
            An example of a semantic validation is to check
            if a child node of a logical not operator ("!") is a 
            filter node.
        """
        self.td_unit = td_unit
        self.parent = parent
        return self


class Comment(ASTNode):

    def __init__(self, comment):
        self.comment = comment

    def __str__(self):
        return self.comment


class Operation(ASTNode):
    """ Representation of an operation. An operation processes one to many 
        entries and produces zero (`[]`) to many entries. An operation which 
        does not apply to an entry/a list of entries returns `None`. 
        For a precise definition of "does not apply" see the documentation 
        of the respective operations.

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
            None needs to be returned.
        - an extractor which extracts one to multiple parts of an entry. 
            An extractor might "extract" the original entry. For example,
            an extractor for numbers might return the original entry if 
            the entry just consists of numbers.
            An extractor which does not extract a single entry is not
            considered to be applicable and None is returned. Hence,
            an extractor never returns an empty list.
        - a filter operation which takes an entry and either returns
            the entry (`[entry]`) or the empty list.
        - a meta operation ("+","*","!") which manipulates the behavior 
            of a filter, an extractor or a transformation. A meta operation
            that manipulates a filter is also considered a filter and a
            meta operation that manipulates an extractor or transformer
            is considered to be of the respective type.        
        - a report operation which may collect some statistics or
            prints out an entry, but always just returns the entry/entries
            as is; with respect to the processing pipeline it is a 
            nop.
        - a macro which combines one to many operations and which basically
            provides a convenience method to facilitate the definition of
            a list of operations which should be carried out in a specific order
            and which may be used multiple times.

        Lifecycle:
        During parsing an operation is created. After parsing has completed
        the initialization is performed in a second step ("init(...)"). After
        that, each entry in a dictionary will be processed. Before a
        new entry is processed "new_entry()" is called to inform the 
        operation that a new dictionary entry will be processed.
        1. __init__ (should not throw errors/exception that may be related to user input)
        2. init (should validate the configuration/setup and throw InitializationFailedExceptions in case of configuration/setup issues!)
        3. <for each entry of a dictionary>:
            3.1 next_entry
            3.1 process_entries
        4. close
    """

    @abstractstaticmethod
    def op_name() -> str:
        """ The operation's name or mnemonic."""
        raise NotImplementedError("subclasses must override this method")

    def __str__(self):
        return self.__class__.op_name()

    def next_entry(self):
        pass

    @abstractmethod
    def process_entries(self, entries: list[str]) -> list[str]:
        """
        Processes each entry of the list and applies the respective operation.

        Returns a list (potentially empty) if the operation could be 
        applied to (at least) some entries. The entries in the given list need
        to be checked if they should be ignored. That is, 
        __`process_entries` is responsible for checking for entries which
        should be explicitly ignored and those which have length zero!__

        Precondition:        
        The given list of entries does not contain duplicates and all entries
        have been checked for not being ignored. I.e., all filter operations
        can pass on the original list if all elements pass the filter.

        Result:
        Returns None if the operation could not be applied. If the operation
        returns new entries, then the list does not contain duplicates and
        none of the entries is ignored.

        Weekly maintains the order of intermediate results. 
        """
        raise NotImplementedError()

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


class Transformer(Operation):
    @final
    def is_transformer(self) -> bool: return True


class Filter(Operation):
    @final
    def is_filter(self) -> bool: return True


class Extractor(Operation):
    @final
    def is_extractor(self) -> bool: return True


class ComplexOperation(ASTNode):
    """ Representation of a sequence of operations.

        Instantiation of a complex operation which is made up of 
        multiple atomic/macro operations. An instance of ComplexOperation 
        basically just handles applying the atomic operations to 
        an entry and (potentially) every subsequently created entry.
    """

    def __init__(self, ops: list[Operation]):
        if not ops or len(ops) == 0:
            # The following exception is related to a programming
            # error! The grammar enforces that a complex
            # operation is never empty. I.e., in that case a
            # syntax error would be signaled and that one would need
            # to be handled by the user.
            raise ValueError(f"no operations: {ops}")
        self.ops = ops

    def __str__(self) -> str:
        return " ".join(map(str, self.ops))

    def is_filter(self) -> bool:
        return \
            any(op.is_filter() for op in self.ops) and \
            all(op.is_filter() or op.is_reporter() for op in self.ops)

    def is_transformer(self) -> bool:
        # is_transformer = False
        # for op in self.ops:
        #    if op.is_transformer():
        #        is_transformer = True
        #    elif op.is_reporter():
        #        pass
        #    else:
        #        return False
        # return is_transformer
        return any(op.is_transformer() for op in self.ops)

    def is_extractor(self) -> bool:
        # is_extractor = False
        # for op in self.ops:
        #    if op.is_extractor():
        #        is_extractor = True
        #    elif op.is_reporter():
        #        pass
        #    else:
        #        return False
        # return is_extractor
        return any(op.is_extractor() for op in self.ops)

    def is_transformer_or_extractor(self) -> bool:
        return any(op.is_transformer_or_extractor() for op in self.ops)

    def is_reporter(self) -> bool:
        return all(op.is_reporter() for op in self.ops)

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        for op in self.ops:
            op.init(td_unit, self)
        return self

    def next_entry(self):
        for op in self.ops:
            op.next_entry()

    def process_entries(self, entries):
        td_unit: TDUnit = self.td_unit
        trace = td_unit.trace
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
                        trace(f"{s_op} => {current_entries}")
                    else:
                        trace(
                            f"{s_op}( {previous_entries} ) => {current_entries}")
            except Exception as e:
                print(traceback.format_exc(), file=stderr)
                print(f"[error] {op}({entries}) failed: {str(e)}", file=stderr)
                exit(-2)

        return current_entries

    def close(self):
        for op in self.ops:
            op.close()


class ListDefinition(ASTNode):
    """
    Represents a named list. A named list is initialized/reset before an
    entry of the dictionary is processed and holds (intermediate) 
    results created while processing the entry.
    """

    def __init__(self, name):
        self.name = name

    def __str__(self) -> str:
        return "list "+self.name

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        td_unit.entry_lists[self.name] = []
        return self


class GlobalListDefinition(ASTNode):
    """
    Represents a named list that will be initialized from the given file.
    Used by special operations that transform entries based on 
    the global list.
    """

    def __init__(self, listname, filename, cop) -> None:
        self.listname = listname
        self.filename = filename
        self.cop = cop

    def __str__(self) -> str:
        cmd = f'global_list {self.listname} "{self.filename}"'
        if self.cop is not None:
            cmd += "( "+str(self.cop)+" )"
        return cmd

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode'):
        super().init(td_unit, parent)
        self.td_unit.global_entry_lists[self.listname] = []
        if self.cop is not None:
            self.cop.init(td_unit, self)
        return self

    def instantiate_global_list(self):
        # we have to read the entries now, because we want to apply
        # the specific rules only to the entries of this file (even
        # if we later join the transformed elements with some other
        # elements)
        entries = read_utf8file(self.filename)
        if self.cop:
            entries = self.cop.process_entries(entries)
        self.td_unit.global_entry_lists[self.listname].extend(entries)
        if self.td_unit.verbose:
            msg = f"[debug] global list {self.listname}: {self.filename} (#{len(entries)})"
            print(msg, file=stderr)


class IgnoreEntries(ASTNode):

    def __init__(self, filename):
        self.filename = filename

    def __str__(self) -> str:
        return "ignore \""+self.filename+"\""

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        # 1. reads in the file and stores the entries to
        #    be ignored in the TDUnit object.
        to_be_ignored = set(read_utf8file(self.filename))
        td_unit.ignored_entries = td_unit.ignored_entries.union(to_be_ignored)
        if td_unit.verbose:
            msg = f"[debug] ignoring: {self.filename} (#{len(to_be_ignored)})"
            print(msg, file=stderr)
        return self


class Generate(ASTNode):

    def __init__(self, mode, raw_config_value):
        self.mode = mode
        self.raw_config_value = raw_config_value
        self.config = None  # will be initialized by init

    def __str__(self) -> str:
        return f"gen {self.mode} {self.raw_config_value}"

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)

        if self.mode == "alt":
            self.config = eval(self.raw_config_value)
        else:
            raise InitializationFailed(f"{self}: unknown generator")

        return self

    def evaluate_generator(self) -> Iterable[str]:
        if self.mode == "alt":
            def gen_alt(s, l_of_l_of_strs):
                if len(l_of_l_of_strs) == 0:
                    yield s
                else:
                    for n in l_of_l_of_strs[0]:
                        yield from gen_alt(s+n, l_of_l_of_strs[1:])
            g = gen_alt("", self.config)
            return g
        else:
            # this code should never be reached!
            raise NotImplementedError


class CreateFile(ASTNode):

    def __init__(self, filename, initial_value):
        self.filename = filename
        self.initial_value = initial_value

    def __str__(self) -> str:
        ending = ""
        if self.initial_value != "":
            ending = f'< "{escape(self.initial_value)}"'
        return f'create "{self.filename}"{ending}'

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        # let's append ... this enables multiple writes to the same file
        # in one TD file
        try:
            file = open_file(self.filename, "w")
            file.write(self.initial_value)
            file.close()
        except Exception as e:
            raise InitializationFailed(f"{self}: failed creating file - {e}")
        return self


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

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        op_module = import_module("operations."+self.module_name)
        op_class_name = "".join(
            map(lambda x: x.capitalize(), self.module_name.split("_"))
        )
        op_class = getattr(op_module, op_class_name)
        value = None
        try:
            old_value = getattr(op_class, self.field_name)
        except AttributeError:
            msg = f"{self}: unknown field name {op_class_name}.{self.field_name}"
            raise InitializationFailed(msg)

        value_type = type(old_value)

        if td_unit.verbose:
            print(
                f"[debug] updating: " +
                f"{op_module.__name__}.{op_class.__name__}.{self.field_name} = " +
                f"{self.field_value} (before: {old_value})",
                file=stderr)

        if value_type == int:
            value = int(self.field_value)
        elif value_type == bool:
            if self.field_value == "True":
                value = True
            elif self.field_value == "False":
                value = False
            else:
                raise ValueError(f"unknown boolean value {self.field_value}")
        elif value_type == float:
            value = float(self.field_value)
        elif value_type == str:
            value = self.field_value
        elif value_type == list:  # this also handles lists of lists...
            value = eval(self.field_value)
        else:
            msg = f"{self} unsupported {value_type}; supported int, bool, float, str, list of <one of the previous>"
            raise InitializationFailed(msg)

        setattr(op_class, self.field_name, value)
        return self


class MacroDefinition(ASTNode):

    def __init__(self, name: str, cop: ComplexOperation):
        self.name = name
        self.cop = cop

    def __str__(self) -> str:
        return "def "+self.name+" "+str(self.cop)

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        # 1. reads in the file and stores the entries to
        #    be ignored in the TDUnit object.
        td_unit.macros[self.name] = self.cop
        self.cop.init(td_unit, self)
        return self

    def close(self):
        self.cop.close()


class Header(ASTNode):

    def __init__(self, setup_ops: list[ASTNode]):
        self.setup_ops = setup_ops

    def __str__(self):
        return "\n".join(str(o) for o in self.setup_ops)

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        for o in self.setup_ops:
            o.init(td_unit, self)
        return self

    def instantiate_global_lists(self):
        for gs in self.setup_ops:
            try:
                gs.instantiate_global_list()
            except:
                pass

    def evaluate_generators(self) -> Iterable[str]:
        its = []
        for o in self.setup_ops:
            try:
                # "only generators support evaluate_generator()"
                g = o.evaluate_generator()
                its.append(g)
            except:
                pass
        return chain(*its)

    def close(self):
        for setup_op in self.setup_ops:
            if isinstance(setup_op, MacroDefinition):
                setup_op.close()


class Body(ASTNode):

    def __init__(self, cops: list[ComplexOperation]):
        self.cops = cops
        # the initialization will be completed by "init"
        self.td_unit = None
        self.parent = None

    def __str__(self):
        return "\n".join(map(str, self.cops))

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        self.td_unit = td_unit
        for cop in self.cops:
            cop.init(td_unit, self)
        return self

    def apply_cops(self, entry: str):
        trace = self.td_unit.trace
        # apply all operations in the specified order on the entry
        for cop in self.cops:
            if not isinstance(cop, Comment):
                if self.td_unit.trace_ops:
                    escaped_entry = entry.replace(
                        "\\", "\\\\").replace("\"", "\\\"")
                    s_cop = str(cop)
                    if s_cop.startswith("use"):
                        trace(f'applying: {s_cop}')
                    else:
                        trace(f'applying: {s_cop}( {escaped_entry} )')
                cop.process_entries([entry])

    def process(self, entry: str):
        # "-1." The ignored check for the entry is done by TDUnit

        # information all operations that a new entry will be processed
        for cop in self.cops:
            if not isinstance(cop, Comment):
                cop.next_entry()

        self.apply_cops(entry)

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

        # A map from str (list name) to current entries.
        self.entry_lists: dict[str, list[str]] = {}
        self.restart_context = []  # list of restart operations and strings
        self.global_entry_lists: dict[str, list[str]] = {}
        # A map from str to complex operation objects
        self.macros: dict[str, ComplexOperation] = {}

        self.print_global_lists = False  # detailed information about global lists is printed
        self.report_progress = False  # report progress w.r.t. the processed entries
        self.trace_ops = False  # provide detailed information about an operation's effect
        self.verbose = False  # provide configuration and initialization related information
        self.unique = False  # controls if a result is only reported once
        self.warn = False

    def __str__(self):
        return str(self.header)+"\n\n"+str(self.body)

    def init(self, td_unit: 'TDUnit', parent: ASTNode):
        super().init(td_unit, parent)
        self.header.init(td_unit, self)
        self.body.init(td_unit, self)
        return self

    def instantiate_global_lists(self):
        self.header.instantiate_global_lists()

    def evaluate_generators(self) -> Iterable[str]:
        return self.header.evaluate_generators()

    def process(self, no: int, entry: str):
        if len(entry) == 0:
            return

        if entry not in self.ignored_entries:
            if self.report_progress:
                print(f"[progress] processing #{no}: {entry}", file=stderr)

            # clear all (intermediate) lists
            for k in self.entry_lists.keys():
                self.entry_lists[k].clear()
            # delegate to the body for the application of the rules
            self.body.process(entry)

        else:
            if self.report_progress:
                print(f"[progress] ignoring   #{no}: {entry}", file=stderr)

    def trace(self, msg):
        if self.restart_context:
            def restart_context_to_str(ctx):
                if isinstance(ctx,tuple):
                    (fe,_re) = ctx
                    #return f'"{escape(fe)}"~"{escape(re)}"'
                    return f'"{escape(fe)}"'
                else:
                    return str(ctx.cop)
            ctx = " - ".join(map(restart_context_to_str, self.restart_context))
            full_msg = f"[trace: {ctx}] {msg}"
        else:
            full_msg = f"[trace] {msg}"
        print(full_msg, file=stderr)

    def close(self):
        self.header.close()
        self.body.close()
