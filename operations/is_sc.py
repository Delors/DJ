from typing import List

from operations.operation import Operation


class IsSpecialChars(Operation):
    """ Identifies entries which only consists of special chars.
    """

    def is_filter(self) -> bool: 
        return True

    _SPECIAL_CHARS = set("^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()[]{}\\-")

    def process(self, entry: str) -> List[str]:
        if any(e for e in entry if e not in self._SPECIAL_CHARS):
            return []        
        else:
            return [entry]

    def __str__(self):
        return "is_sc"   

IS_SPECIAL_CHARS = IsSpecialChars()