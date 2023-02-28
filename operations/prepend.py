from typing import List

from dj_ast import TDUnit, ASTNode
from dj_ast import Transformer
from common import InitializationFailed,escape


class Prepend(Transformer):
    """ Prepends a given string to (each character of) an entry.

        E.g., to convert an entry such that it can be prepended to a 
        term using Hashcat's prepend rule a combination of this rule 
        with `reverse` can be used.

            reverse prepend each "^"
            
        If you want to create a Hashcat append rule out of an entry:
        
            prepend each "$"
        
        is sufficient.
    """

    def op_name() -> str: return "prepend"

    def __init__(self, prepend_each: bool, s: str):
        self.prepend_each = prepend_each
        self.s = s

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.s) == 0 :
            msg = f"{self}: useless prepend operation"
            raise InitializationFailed(msg)
        return self

    def process(self, entry: str) -> List[str]:
        if len(entry) > 0:
            if self.prepend_each:
                return [self.s + (self.s.join(entry))]
            else:
                return [self.s + entry]
        else: 
            return [entry]


    def __str__(self):
        m = ""
        if self.prepend_each:
            m = " each"
        return f'{Prepend.op_name()}{m} "{escape(self.s)}"'
