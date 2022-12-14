from typing import List

from operations.operation import Filter


class IsSpecialChars(Filter):
    """ Identifies entries which only consist of special chars.
    """

    SPECIAL_CHARS = set("^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()[]{}\\-")

    def process(self, entry: str) -> List[str]:
        if any(e for e in entry if e not in self.SPECIAL_CHARS):
            return []        
        else:
            return [entry]

    def __str__(self):
        return "is_sc"   

IS_SPECIAL_CHARS = IsSpecialChars()