from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from operations.operation import Operation

class Lower(Operation):
    """Converts an entry to all lower case."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        lower = entry.lower()
        if lower != entry:
            return [lower]
        else:
            return None

    def __str__(self):
        return "lower"    

LOWER = Lower()  