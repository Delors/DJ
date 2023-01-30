from typing import List

from dj_ast import ASTNode, TDUnit, Filter
from common import InitializationFailed


class Max(Filter):
    """Only accepts entries with a given maximum number of the specified character class."""

    def op_name() -> str: return "max"

    def _test_length(c: str) -> bool: return True
    def _test_lower(c: str) -> bool: return c.islower()
    def _test_upper(c: str) -> bool: return c.isupper()
    def _test_numeric(c: str) -> bool: return c.isnumeric()
    def _test_alpha(c: str) -> bool: return c.isalpha()
    def _test_not_alpha(c: str) -> bool: return not c.isalpha()
    def _test_symbol(c: str) -> bool: return not c.isalnum()

    _tests = {
        "length": _test_length,
        "lower": _test_lower,
        "upper": _test_upper,
        "numeric": _test_numeric,
        "letter": _test_alpha,
        "symbol": _test_symbol,
        "non_letter": _test_not_alpha
    }

    def __init__(self, operator: str, max_count: int):
        self.operator = operator
        self.test = self._tests[operator]
        self.max_count = max_count

    def init(self, td_unit: TDUnit, parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        max_count = self.max_count
        if max_count < 0:
            msg = f"max {self.operator} has to be >= 0 (actual {max_count})"
            raise InitializationFailed(msg)


    def process(self, entry: str) -> List[str]:
        count = 0
        for c in entry:
            if self.test(c):
                count += 1
                if count > self.max_count:
                    return []

        return [entry]

    def __str__(self):
        return f"{Max.op_name()} {self.operator} {self.max_count}"
