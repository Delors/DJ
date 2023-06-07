from functools import partial

from common import InitializationFailed
from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryFilter


class Min(PerEntryFilter):
    """ Only accepts entries with a given minimum number of characters of
        the specified character class.
    """

    def _test_length(entry: str, min_count: int) -> list[str]:
        return [entry] if len(entry) >= min_count else []

    def _test_unique(entry: str, min_count: int) -> list[str]:
        cs = set()
        count = 0
        for c in entry:
            if c not in cs:
                count += 1
                if count >= min_count:
                    return [entry]
                cs.add(c)
        return []

    def _test_lower(c: str) -> bool: return c.islower()
    def _test_upper(c: str) -> bool: return c.isupper()
    def _test_numeric(c: str) -> bool: return c.isnumeric()
    def _test_alpha(c: str) -> bool: return c.isalpha()
    def _test_not_alpha(c: str) -> bool: return not c.isalpha()
    def _test_symbol(c: str) -> bool: return not c.isalnum()

    def _count(entry, min_count, f) -> list[str]:
        count = 0
        for c in entry:
            if f(c):
                count += 1
                if count >= min_count:
                    return [entry]
        return []

    _tests = {
        "length": _test_length,
        "lower": partial(_count, f=_test_lower),
        "upper": partial(_count, f=_test_upper),
        "numeric": partial(_count, f=_test_numeric),
        "letter": partial(_count, f=_test_alpha),
        "symbol": partial(_count, f=_test_symbol),
        "non_letter": partial(_count, f=_test_not_alpha),
        "unique": _test_unique
    }

    def op_name() -> str: return "min"

    def __init__(self, operator: str, min_count: int):
        self.operator = operator
        self.test = None
        self.min_count = min_count

    def __str__(self):
        return f"{Min.op_name()} {self.operator} {self.min_count}"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        try:
            self.test = self._tests[self.operator]
        except:
            msg = f"{self}: unsupported operator ({', '.join(self._tests.keys())})"
            raise InitializationFailed(msg)

        if self.min_count <= 0:
            raise InitializationFailed(
                f"{self}: min {self.operator} {self.min_count} has to be > 0")
        return self

    def process(self, entry: str) -> list[str]:
        return self.test(entry, self.min_count)
