from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryTransformer
from common import InitializationFailed, escape


class PosMap(PerEntryTransformer):
    """ Maps each character at every position to a character from the 
        given set of characters.

        For example:
        Given the operation:
            pos_map "ab"
        and the dictionary entry:
            Test
        PosMap will generate the following output:
            aest
            best
            Tast
            Tbst
            Teat
            Tebt
            Tesa
            Tesb
    """

    def op_name() -> str: return "pos_map"

    def __init__(self, target_chars: str):
        self.raw_target_chars = target_chars
        self.target_chars = set(target_chars)

    def __str__(self):
        target_chars = escape(self.raw_target_chars)
        return f'{PosMap.op_name()} "{target_chars}"'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if (len(self.target_chars) == 0):
            raise InitializationFailed(
                f"{self}: pos_map's target chars must not be empty")
        return self

    def process(self, entry: str) -> list[str]:
        entries = []
        entry_len = len(entry)
        for i in range(0, entry_len):
            for c in self.target_chars:
                entries.append(entry[0:i]+c+entry[i+1:entry_len])

        return entries
