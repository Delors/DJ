from abc import ABC,abstractmethod
from typing import List
from importlib import import_module
from sys import stderr

from common import InitializationFailed, read_utf8file

class ASTNode(ABC):

    def init(self, spec : 'TDFile', parent : 'ASTNode', verbose: bool): 
        """ Performs a semantic validation and initialization 
            of this node and then calls the method on child nodes. 
            
            In case of an error a ValidationError is raised. 
            An example, of a semantic validation is to check
            if a child node of a logical not operator ("!") is a 
            filter node.

            Validate only checks for conceptual errors. 
        """
        pass


class Comment(ASTNode):
    def __init__(self,comment):
        self.comment = comment
    def __str__(self):
        return self.comment


class Operation(ASTNode):
    """ Representation of an operation. An operation processes one to many entries
      and produces zero (`[]`) to many entries. An operation which 
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
        considered to be applicable and None is returned.
      - a meta operation which manipulates the behavior of a filter,
        an extractor or a transformation.
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
    """

    @staticmethod 
    @abstractmethod
    def op_name() -> str: 
        """ The operation's name need to be set by an operation! """
        raise NotImplementedError()
        

    def init(self, spec: 'TDFile', parent: 'ASTNode', verbose : bool):
      pass

    def process_entries(self, entries : List[str]) -> List[str]:
        """
        Processes each entry of the list and applies the respective operation.

        Returns the empty list if the operation could be applied to (at least)
        some entries in these cases returned the empty list.

        Returns None if the operation could not be applied. 
        """
        all_none = True
        all_new_entries = []
        for entry in entries:
          new_entries = self.process(entry)
          if new_entries is not None:
            all_none = False
            all_new_entries.extend(new_entries)
        if all_none:
          return None
        else:
          return all_new_entries
    
    def process(self, entry: str) -> List[str]:
        """
        Processes the given entry and returns the list of new entries.
        If an operation applies, i.e., the operation has some effect, 
        a list of new entries (possibly empty) will be returned.
        If an operation does not apply at all, None should be returned.
        Each operation has to clearly define when it applies and when not.

        For example, an operation to remove special chars would apply to
        an entry consisting only of special chars and would return
        the empty list in that case. If, however, the entry does not 
        contain any special characters, None would be returned.

        E.g., an operation that just extracts certain characters or which 
        replaces certain characters will always either return a 
        non-empty list (`[]`) or `None` (didn't apply).
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
    """ Representation of a complex operation.

        Instantiation of a complex operation which is made up of 
        multiple atomic/macro operations. An instance of ComplexOperation 
        basically just handles applying the atomic operations to 
        an entry and (potentially) every subsequently created entry.
    """

    def __init__(self, ops: List[Operation]):
        if not ops or len(ops) == 0:
            raise ValueError(f"missing operations: {ops}")
        self.ops = ops
        return
    def __str__(self) -> str:
        return " ".join(map(str,self.ops))


    def init(self, spec: 'TDFile', parent: ASTNode, verbose : bool):
        for op in self.ops: op.init(spec,self,verbose)

    def apply(self, entry):
        return apply_ops(entry,self.ops)

    def close(self):
        for op in self.ops: op.close()    


class SetDefinition(ASTNode):
    def __init__(self,name):
        self.name = name
    def __str__(self) -> str:
        return "set "+self.name

    def init(self, spec: 'TDFile', parent: ASTNode, verbose: bool):
        spec.entry_sets[self.name] = []

class IgnoreEntries(ASTNode):
    def __init__(self,filename):
        self.filename = filename
    def __str__(self) -> str:
        return "ignore \""+self.filename+"\""

    def init(self, spec: 'TDFile', parent: ASTNode, verbose: bool):
        # 1. reads in the file and stores the entries to
        #    be ignored in the TDFile object.
        spec.ignored_entries.union(set(read_utf8file(self.filename)))

class ConfigureOperation(ASTNode):
    def __init__(self,module_name,field_name,field_value):
        self.module_name = module_name
        self.field_name = field_name
        self.field_value = field_value
    def __str__(self):
        return \
            "config "+\
            self.module_name+" "+\
            self.field_name+" "+\
            self.field_value

    def init(self, spec: 'TDFile', parent: ASTNode, verbose: bool):
        op_module = import_module("operations."+self.module_name)
        op_class_name = "".join(
                map (lambda x: x.capitalize(), self.module_name.split("_"))
            )
        op_class = getattr(op_module,op_class_name)
        value = None
        try:
            old_value = getattr(op_class,self.field_name)
        except AttributeError:
            msg = f"unknown field name: {op_class_name}.{self.field_name}"
            raise InitializationFailed(msg)

        if verbose:
            print(
                f"[debug] updating:"+
                f"{op_module.__name__}.{op_class.__name__}.{self.field_name} = "+
                f"{self.field_value} (old value:{old_value})",file=stderr)

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

        setattr(op_class,self.field_name,value)            

class MacroDefinition(ASTNode):
    def __init__(self,name : str,cop : ComplexOperation):
        self.name = name
        self.cop = cop
    def __str__(self) -> str:
        return "def "+self.name+" "+str(self.cop)

    def init(self, spec: 'TDFile', parent: ASTNode, verbose : bool):
        # 1. reads in the file and stores the entries to
        #    be ignored in the TDFile object.
        spec.macros[self.name] = self.cop
        self.cop.init(spec,self,verbose)

class Header(ASTNode):
    def __init__(self, setup_ops : List[ASTNode]):
        unwrapped_setup_ops = map(lambda x : x[0],setup_ops)
        self.setup_ops : List[ASTNode] =\
           [ so for so in unwrapped_setup_ops if so is not None ]
    def __str__(self):
        return "\n".join(str(o) for o in self.setup_ops)
    def init(self, spec: 'TDFile', parent: ASTNode, verbose : bool):
        for o in self.setup_ops: o.init(spec,self,verbose)

class Body(ASTNode):
    def __init__(self, ops : List[ComplexOperation]):
        unwrapped_ops = map(lambda x : x[0],ops)
        self.ops : List[ComplexOperation] =\
            [ o for o in unwrapped_ops if o is not None ]
    def __str__(self):
        return "\n".join(str(o) for o in self.ops)
    def init(self, spec: 'TDFile', parent: ASTNode, verbose : bool):
        for o in self.ops: o.init(spec,self,verbose)        

class TDFile(ASTNode):
    def __init__(self, header : Header, body : Body):
        self.header = header
        self.body = body
        # The following fields will be fully initialized during 
        # the explicit initialization step.
        self.ignored_entries : set[str] = set()
        self.entry_sets = {} # A map from str (set name) to current entries.
        self.macros = {}
    def __str__(self):
        return str(self.header)+"\n\n"+str(self.body)
    def init(self, spec: 'TDFile', parent: ASTNode, verbose : bool):
        self.header.init(spec,self,verbose)
        self.body.init(spec,self,verbose)        