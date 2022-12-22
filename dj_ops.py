from typing import List
from sys import stderr

from common import enrich_filename

from dj_ast import Operation
from dj_ast import ComplexOperation
from dj_ast import TDFile
from dj_ast import ASTNode


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

    def op_name() -> str: return "report"

    def is_reporter(self) -> bool: return True   

    def process(self, entry: str) -> List[str]:
        report(entry)
        return [entry]


REPORT = Report()        


class Write(Report):

    def op_name() -> str: return "write"

    def __init__(self,filename) -> None:
        super().__init__()
        self.filename = filename
        self.file = open(enrich_filename(filename),"w",encoding="utf-8")

    def is_reporter(self) -> bool: return True   

    def process(self, entry: str) -> List[str]:
        print(entry,file=self.file)
        return [entry]

    def close(self):
        try:
            self.file.close()
        except Exception as e:
            print(f"failed closing {self.filename}",file=stderr)
            pass
               
    def __str__(self):
        return f"{Write.op_name()} \"{self.filename}\""



class Use(Operation):

    def op_name() -> str: return "use"

    def __init__(self,setname) -> None:
        super().__init__()
        self.setname = setname

    def process(self, entry: str) -> List[str]:
        return sets[self.setname]
               
    def __str__(self):
        return f"{Use.op_name()} {self.setname}" 

class StoreInSet(Operation):

    def op_name() -> str: return "store_in"

    def __init__(self,setname,ops : ComplexOperation) -> None:
        super().__init__()
        self.setname = setname
        self.ops = ops

    def process(self, entry: str) -> List[str]:
        return entry
               
    def __str__(self):
        return f"{StoreInSet.op_name()} {self.setname}({self.ops})" 


class StoreFilteredInSet(Operation):

    def op_name() -> str: return "store_filtered_in"

    def __init__(self,setname,ops : ComplexOperation) -> None:
        super().__init__()
        self.setname = setname
        self.ops = ops

    def process(self, entry: str) -> List[str]:
        return entry
               
    def __str__(self):
        return f"{StoreFilteredInSet.op_name()} {self.setname}({self.ops})" 



class MacroCall(Operation):
    """Represents a macro call."""

    def op_name() -> str: return "do"

    def __init__(self, name :str, ops : List[Operation]): # TODO set ops in init step
        self.name = name
        self.ops = ops
        return

    def is_macro(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        return apply_ops(entry,self.ops)

    def close(self):
        for op in self.ops: op.close()    

    def __str__(self):
        return f"{MacroCall.op_name()} {self.name}"


class KeepAlwaysModifier(Operation):
    """ Modifies the behavior of the wrapped transformer/extractor
        such that all input entries will also be output entries 
        additionally to those that are newly created by the 
        wrapped operation.
    """

    def op_name() -> str: return "+"

    def __init__(self, op : Operation):
        self.op = op

        if not op.is_transformer() and not op.is_extractor():
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = []
        entries.append(entry)
        return entries
        
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

    def __init__(self, op : Operation):
        self.op = op

        if not (op.is_transformer() or op.is_extractor()):
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = [entry]
        return entries
        
    def __str__(self):
        return KeepOnlyIfFilteredModifier.op_name() + str(self.op)        


class NegateFilterModifier(Operation):
    """ Modifies the behavior of the wrapped filter such that if the 
        given entry is returned by the underlying filter, an empty 
        list will be returned and vice versa.
    """

    def op_name() -> str : return "!"

    def __init__(self, op : Operation):
        self.op = op

        if not (op.is_filter()):
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries == []:
            return [entry]
        else:
            return []
        
    def __str__(self):
        return NegateFilterModifier.op_name() + str(self.op)        

class Or(Operation):

    def op_name() -> str : return "or"

    def __init__(self, cops : List[ComplexOperation]) -> None:
        self.cops = cops

    def __str__(self):
        cops = ", ".join(map (lambda x: str(x), self.cops))
        return Or.op_name() +"(" + cops + ")"