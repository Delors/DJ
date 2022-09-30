import re
from typing import List

from operations.operation import Operation


class RemoveNumbers(Operation):
    """Removes all numbers from an entry."""

    re_no_numbers = re.compile("[^0-9]+")

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveNumbers.re_no_numbers.finditer(entry)
        ]
        if len(entries) == 0:
            return []
        elif entry != entries[0]:
            return ["".join(entries)]
        else:
            return None

    def __str__(self):
        return "remove_numbers"   

REMOVE_NUMBERS = RemoveNumbers()