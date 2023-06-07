from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryTransformer
from common import InitializationFailed


class Lower(PerEntryTransformer):
    """ Converts the complete entry or the character at the 
        specified index to lower case. I.e., standard usage is:

            lower
        or 
            lower <INT_VALUE>

        One use case is to ensure that the first letter is
        always a lower case letter.
    """

    def op_name() -> str: return "lower"

    def __init__(self, pos: int = None) -> None:
        self.pos = pos

    def __str__(self):
        if self.pos:
            return f"{Lower.op_name()} {self.pos}"
        else:
            return Lower.op_name()

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.pos is not None and self.pos < 0:
            raise InitializationFailed(f"{self}: pos has to be >= 0")
        return self

    def process(self, entry: str) -> list[str]:
        pos = self.pos
        if pos is None:
            lower = entry.lower()
        else:
            if len(entry) > pos:
                lower = entry[0:pos] + entry[pos].lower() + entry[pos+1:]
            else:
                lower = entry

        if lower != entry:
            return [lower]
        else:
            return None
