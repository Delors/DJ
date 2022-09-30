import re
from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from operations.operation import Operation


class GetSpecialChars(Operation):
    """Extracts the used special char (sequences)."""

    #re_special_chars = re.compile("[^a-zA-Z0-9\s]+")
    re_special_chars = re.compile("[<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-]+")

    def is_extractor(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetSpecialChars.re_special_chars.finditer(entry)
        ]
        if len(entries) >= 1:
            return entries
        else:
            return None

    def __str__(self):
        return "get_sc"

GET_SPECIAL_CHARS = GetSpecialChars()
