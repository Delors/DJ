from typing import List

from operations.operation import Operation


class MaxLength(Operation):
    """Only accepts entries with a given maximum length."""

    def __init__(self, max_length : int):
        self.max_length = max_length
        return

    def is_filter(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if len(entry) <= self.max_length:
            return [entry]
        else:
            return []

    def __str__(self):
        return f"max_length {self.max_length}"
