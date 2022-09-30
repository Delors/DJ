from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from operations.operation import Operation

class MinLength(Operation):
    """Only accepts entries with a given minimum length."""

    def __init__(self, min_length : int):
        self.min_length = min_length
        return

    def is_filter(self) -> bool:
        return True

    def process(self, entry: str) -> List[str]:
        if len(entry) >= self.min_length:
            return [entry]
        else:
            return []

    def __str__(self):
        return f"min_length {self.min_length}"

