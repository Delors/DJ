import re
from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from operations.operation import Operation


class GetNumbers(Operation):
    """Extracts all numbers."""

    re_numbers = re.compile("[0-9]+")

    def is_extractor(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetNumbers.re_numbers.finditer(entry)
        ]
        if len(entries) >= 1:
            return entries
        else:
            return None

    def __str__(self):
        return "get_numbers"   

GET_NUMBERS = GetNumbers()