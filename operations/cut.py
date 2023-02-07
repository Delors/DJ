from typing import List

from dj_ast import Extractor
from common import InitializationFailed


class Cut(Extractor):
    """
    Cuts the left or right characters of a term.
    """

    def op_name() -> str: return "cut"

    def __init__(self, operator: str, min: int, max: int):
        self.operator = operator  # cut left == "l" or right == "r"...
        self.min = min
        self.max = max

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        if self.operator != "l" and self.operator != "r":
            raise InitializationFailed(
                f"operator ({self.operator}) invalid")
        if self.min < 0:
            raise InitializationFailed(
                f"{self.min} has to be >= 0")
        if self.max < self.min:
            raise InitializationFailed(
                f"invariant not satisfied {self.min} < {self.max}")

    def process(self, entry: str) -> List[str]:
        if len(entry) < self.min:
            return None

        new_entries = []
        for i in range(self.min, min(len(entry), self.max)+1):
            if self.operator == "l":
                new_entries.append(entry[i:])
            else:
                new_entries.append(entry[:-i])

        return new_entries

    def __str__(self):
        return f"{Cut.op_name()} {self.operator} {self.min} {self.max}"
