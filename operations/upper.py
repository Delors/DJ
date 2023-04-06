from typing import List

from common import InitializationFailed
from dj_ast import Transformer, TDUnit, ASTNode



class Upper(Transformer):
    """Converts an entry or the specific character to all upper case."""

    def op_name() -> str: return "upper"


    def __init__(self, pos : int = None, letter_with_index : bool = False) -> None:
        self.pos = pos
        self.letter_with_index = letter_with_index

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.pos is not None and self.pos < 0:
            raise InitializationFailed(f"{self}: pos has to be >= 0")

    def process(self, entry: str) -> List[str]:
        pos = self.pos
        if pos is None:
            upper = entry.upper()
        elif not self.letter_with_index:
            if len(entry) > pos:
                upper = entry[0:pos] + entry[pos].upper() + entry[pos+1:]
            else:
                upper = entry
        else:
            upper = ""
            i = 0
            for c in entry:
                if c.isalpha():
                    if i == pos:
                        upper += c.upper()
                    else:
                        upper += c
                    i += 1
                else:
                    upper += c

        if upper != entry:
            return [upper]
        else:
            return None

    def __str__(self):
        if self.pos is not None:
            pos = str(self.pos)
            if self.letter_with_index:
                pos = "l"+pos
            return f"{Upper.op_name()} {pos}"
        else:
            return Upper.op_name()