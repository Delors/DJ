from typing import List

from operations.operation import Filter


class MaxLength(Filter):
    """Only accepts entries with a given maximum length."""

    def __init__(self, max_length : int):
        if max_length <= 0:
            raise ValueError("max_length has to > 0")

        self.max_length = max_length
        return

    def process(self, entry: str) -> List[str]:
        if len(entry) <= self.max_length:
            return [entry]
        else:
            return []

    def __str__(self):
        return f"max_length {self.max_length}"
