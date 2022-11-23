from typing import List

from operations.operation import Filter

class MinLength(Filter):
    """Only accepts entries with a given minimum length."""

    def op_name() -> str: return "min_length"

    def __init__(self, min_length : int):
        if min_length < 0:
            raise ValueError("min_length has to be >= 0")

        self.min_length = min_length
        return

    def process(self, entry: str) -> List[str]:
        if len(entry) >= self.min_length:
            return [entry]
        else:
            return []

    def __str__(self):
        return f"{MinLength.op_name()} {self.min_length}"

