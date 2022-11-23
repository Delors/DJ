import re
from typing import List

from operations.operation import Transformer


class RemoveSpecialChars(Transformer):
    """ Removes all special chars; whitespace is not considered as a
        special char. In general it is recommend to remove/fold 
        whitespace and/or strip the entries afterwards.
    """

    def op_name() -> str: return "remove_sc"

    NON_SPECIAL_CHARACTERS_REGEXP = \
        "[^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-]+"

    #re_non_special_char = re.compile("[a-zA-Z0-9\s]+")
    def __init__(self):
        self._re_non_special_char = \
            re.compile(self.NON_SPECIAL_CHARACTERS_REGEXP)

    def process(self, entry: str) -> List[str]:
        re_non_special_char = self._re_non_special_char        
        entries = [i.group(0) for i in re_non_special_char.finditer(entry)]
        if len(entries) == 0:
            # the entry just consisted of special chars...
            return []
        elif entry != entries[0]:
            return ["".join(entries)]
        else:
            # there were no special chars
            return None


REMOVE_SPECIAL_CHARS = RemoveSpecialChars()