from common import InitializationFailed

from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryTransformer


class Multiply(PerEntryTransformer):
    """
    Multiplies the given term. 

    E.g. `multiply 2`  will transform "Test" to "TestTest".
    """

    def op_name() -> str: return "multiply"

    def __init__(self, factor: int) -> None:
        self.factor = factor

    def __str__(self):
        return f"{Multiply.op_name()} {self.factor}"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.factor <= 1:
            msg = f"{self}: the multiplication factor has to be > 1"
            raise InitializationFailed(msg)

    def process(self, entry: str) -> list[str]:
        return [entry*self.factor]
