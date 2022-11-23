import re
from typing import List

from operations.operation import Extractor


class GetNumbers(Extractor):
    """Extracts all numbers."""

    def op_name() -> str: return "get_numbers"

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


GET_NUMBERS = GetNumbers()