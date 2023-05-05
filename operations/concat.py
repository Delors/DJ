from typing import List

from dj_ast import TDUnit, ASTNode
from dj_ast import Transformer
from common import InitializationFailed,escape


class Concat(Transformer):
    """ Concats all current intermediate results. 
        None is returned if the current set only consists of one 
        intermediate result.
    """

    def op_name() -> str: return "concat"

    def __init__(self, s: str = ""):
        """
        s Str used to concat the entries.
        """
        self.s = s

    def process_entries(self, entries: List[str]) -> List[str]:
        if len(entries) == 1:
            return None

        new_entry = self.s.join(entries)
        if not new_entry in self.td_unit.ignored_entries:
            return [new_entry]

    def __str__(self):
        if len(self.s) > 0 :
            return f'{Concat.op_name()} "{escape(self.s)}"'
        else:
            return f'{Concat.op_name()}'

CONCAT = Concat()