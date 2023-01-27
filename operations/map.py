from typing import List

from dj_ast import Transformer, TDUnit, ASTNode
from common import InitializationFailed, escape


class Map(Transformer):
    """ Maps a given character to several alternatives.
    """

    def op_name() -> str: return "map"

    def __init__(self, source_char: str, target_chars: str):
        self.source_char = source_char
        self.raw_target_chars = target_chars
        self.target_chars = set(target_chars)

    def init(self, td_unit: TDUnit, parent: ASTNode, verbose: bool):
        super().init(td_unit,parent,verbose)
        if not set(self.source_char).isdisjoint(self.target_chars):
            msg = f'useless identity mapping {self.source_char} => "{", ".join(self.target_chars)}"'
            raise InitializationFailed(msg)

    def process(self, entry: str) -> List[str]:
        if self.source_char in entry:
            entries = []
            for c in self.target_chars:
                entries.append(entry.replace(self.source_char, c))
            return entries
        else:
            return None

    def __str__(self):
        source_char = escape(self.source_char)
        target_chars = escape(self.raw_target_chars)
        return f'{Map.op_name()} "{source_char}" "{target_chars}"'
