from typing import List

from operations.operation import Filter

class Min(Filter):
    """Only accepts entries with a given minimum number of the specified character class."""

    def _test_lower(c : str) -> bool : return c.islower()
    def _test_upper(c : str) -> bool : return c.isupper()
    def _test_numeric(c : str) -> bool : return c.isnumeric()
    def _test_alpha(c : str) -> bool : return c.isalpha()
    def _test_not_alpha(c : str) -> bool : return not c.isalpha()
    def _test_symbol(c : str) -> bool : return not c.isalnum()

    _tests = {
        "lower" : _test_lower,
        "upper" : _test_upper,
        "numeric" : _test_numeric,
        "letter" : _test_alpha,
        "symbol" : _test_symbol,
        "non_letter" : _test_not_alpha
    }

    def __init__(self, operator: str, min_count : int):
        if min_count <= 0:
            raise ValueError(f"min_count ({min_count}) has to be > 0")

        self.operator = operator
        self.test = self._tests[operator]
        self.min_count = min_count
        return

    def process(self, entry: str) -> List[str]:
        count = 0
        for c in entry:
            if self.test(c):
                count += 1
                if count >= self.min_count:
                    return [entry]
        
        return []

    def __str__(self):
        return f"min {self.operator} {self.min_count}"

