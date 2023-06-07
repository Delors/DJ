from dj_ast import ASTNode, TDUnit
from dj_ops import Filter
from common import InitializationFailed


class ISetMax(Filter):
    """Only accepts a list of entries with a maximum number of ....
    """

    def _test_length(entries: list[str], max_count: int) -> bool: 
        return len(entries) <= max_count

    _tests = {
        "length": _test_length
    }

    def op_name() -> str: return "iset_max"

    def __init__(self, operator: str, max_count: int):
        self.operator = operator
        self.test = None
        self.max_count = max_count

    def __str__(self):
        return f"{ISetMax.op_name()} {self.operator} {self.max_count}"        

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        try:
            self.test = self._tests[self.operator]
        except:
            msg = f"{self}: unsupported operator ({', '.join(self._tests.keys())})"
            raise InitializationFailed(msg)
        max_count = self.max_count
        if max_count < 0:
            msg = f"{self}: iset_max {self.operator} has to be >= 0 (actual {max_count})"
            raise InitializationFailed(msg)
        return self

    def process_entries(self, entries: list[str]) -> list[str]:
        test = self.test(entries,self.max_count)
        if test:
            return entries
        else:
            return []

