from typing import List

from dj_ast import TDUnit, ASTNode
from dj_ast import Transformer
from common import InitializationFailed,escape


class Append(Transformer):
    """ Appends a given string to (each character of) an entry.

        Please note that the append operation cannot be used
        to create Hashcat append rules out of an entry; for 
        that you have to use prepend operations.
    """

    def op_name() -> str: return "append"

    def __init__(self, append_each: bool, s: str):
        self.append_each = append_each
        self.s = s

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.s) == 0 :
            msg = f"{self}: useless append operation"
            raise InitializationFailed(msg)
        return self

    def process(self, entry: str) -> List[str]:
        if len(entry) > 0:
            if self.append_each:
                return [(self.s.join(entry))+ self.s ]
            else:
                return [entry + self.s]
        else: 
            return [entry]


    def __str__(self):
        m = ""
        if self.append_each:
            m = " each"
        return f'{Append.op_name()}{m} "{escape(self.s)}"'
