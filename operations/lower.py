from typing import List
from common import InitializationFailed

from dj_ast import Transformer, TDUnit, ASTNode


class Lower(Transformer):
    """ Converts the complete entry or a specified 
        character to lower case. I.e., standard usage is:

            lower
        or 
            lower <INT_VALUE>

        One use case is to ensure that the first letter is
        always a lower case letter.
    """

    def op_name() -> str: return "lower"

    def __init__(self, pos : int = None) -> None:
        self.pos = pos

    def init(self, td_unit: TDUnit, parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        if self.pos is not None and self.pos < 0:
            raise InitializationFailed(f"{self}: pos has to be >= 0")

    def process(self, entry: str) -> List[str]:
        if self.pos is None:
            lower = entry.lower()
        else:
            pos = self.pos
            if len(entry) > pos:
                lower = entry[0:pos] + entry[pos].lower() + entry[pos+1:]

        if lower != entry:
            return [lower]
        else:
            return None


    def __str__(self):
        if self.pos:
            return f"{Lower.op_name()} {self.pos}"
        else:
            return Lower.op_name()
