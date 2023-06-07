from functools import partial

from dj_ast import ASTNode, TDUnit, Filter
from common import InitializationFailed


class Has(Filter):
    """Only accepts entries with a given number of characters
       of the specified character class. Basically just combines
       min ... X max ... X.
    """

    def op_name() -> str: return "has"

    def _test_length(entry: str, has_count: int) -> list[str]:
        return [entry] if len(entry) == has_count else []

    def _test_unique(entry: str, has_count: int) -> list[str]:
        cs = set()
        count = 0
        for c in entry:
            if c not in cs:
                count += 1
                if count > has_count:
                    return []
                cs.add(c)
        return [entry] if count == has_count else []

    def _test_lower(c: str) -> bool: return c.islower()
    def _test_upper(c: str) -> bool: return c.isupper()
    def _test_numeric(c: str) -> bool: return c.isnumeric()
    def _test_alpha(c: str) -> bool: return c.isalpha()
    def _test_not_alpha(c: str) -> bool: return not c.isalpha()
    def _test_symbol(c: str) -> bool: return not c.isalnum()

    def _count(entry, has_count, f) -> list[str]:
        count = 0
        for c in entry:
            if f(c):
                count += 1
                if count > has_count:
                    return []
        return [entry] if count == has_count else []

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

    def __init__(self, operator: str, has_count: int):
        self.operator = operator
        self.test = None
        self.has_count = has_count

    def __str__(self):
        return f"{Has.op_name()} {self.operator} {self.has_count}"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        try:
            self.test = self._tests[self.operator]
        except:
            raise InitializationFailed(
                f"{self}: unsupported operator ({', '.join(self._tests.keys())})")
        has_count = self.has_count
        if has_count < 0:
            msg = f"{self}: has {self.operator} has to be >= 0 (actual {has_count})"
            raise InitializationFailed(msg)
        return self

    def process(self, entry: str) -> list[str]:
        return self.test(entry, self.has_count)
