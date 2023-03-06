from typing import List

from matplotlib.transforms import Transform
from common import InitializationFailed

from dj_ast import ASTNode, TDUnit, Transformer


class Multiply(Transformer):
    """
    Dup.

    E.g. "Test" will be transformed to "TestTest".
    """

    def op_name() -> str: return "multiply"

    def __init__(self, factor : int) -> None:
        self.factor = factor

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.factor == 0:
            raise InitializationFailed(f"{self}: the multiplication factor has to be > 0")

    def process(self, entry: str) -> List[str]:
        return [entry*self.factor]

    def __str__(self):
        return f"{Multiply.op_name()} {self.factor}"

