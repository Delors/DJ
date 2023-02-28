from typing import List

from dj_ast import Transformer, TDUnit, ASTNode
from common import InitializationFailed, escape


class Remove(Transformer):
    """Removes all those characters of an entry that are found in the specified list."""

    def op_name() -> str: return "remove"


    def __init__(self, chars: str):
        self.chars = chars
        self.chars_set = set()

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.chars) == 0:
            raise InitializationFailed(
                f"{self}: invalid length for chars")
        self.chars_set = set(self.chars)
        if len(self.chars_set) != len(self.chars):
            msg = f'{self}: specified set contains duplicates'
            raise InitializationFailed(msg)
        return self

    def process(self, entry: str) -> List[str]:
        new_entry = "".join(c for c in entry if c not in self.chars_set)
        if new_entry != entry:
            if len(new_entry) == 0:
                return []
            else:
                return [new_entry]
        else:
            return None

    def __str__(self):        
        chars = escape(self.chars)
        return f'{Remove.op_name()} "{chars}"'
