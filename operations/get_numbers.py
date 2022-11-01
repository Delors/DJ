import re
from typing import List

from operations.operation import Extractor


class GetNumbers(Extractor):
    """Extracts all numbers."""

    _re_numbers = re.compile("[0-9]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetNumbers._re_numbers.finditer(entry)
        ]
        if len(entries) >= 1:
            return entries
        else:
            return None

    def __str__(self):
        return "get_numbers"   

GET_NUMBERS = GetNumbers()