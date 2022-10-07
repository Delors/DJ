import re
from typing import List

from operations.operation import Operation


class RemoveSpecialChars(Operation):
    """ Removes all special chars; whitespace is not considered as a
        special char. In general it is recommend to remove/fold whitespace
        and/or strip the entries afterwards.
    """

    #re_non_special_char = re.compile("[a-zA-Z0-9\s]+")
    re_non_special_char = \
        re.compile("[^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-]+")

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        re_non_special_char = RemoveSpecialChars.re_non_special_char        
        entries = [i.group(0) for i in re_non_special_char.finditer(entry)]
        if len(entries) == 0:
            # the entry just consisted of special chars...
            return []
        elif entry != entries[0]:
            return ["".join(entries)]
        else:
            # there were no special chars
            return None

    def __str__(self):
        return "remove_sc"

REMOVE_SPECIAL_CHARS = RemoveSpecialChars()