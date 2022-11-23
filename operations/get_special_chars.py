import re
from typing import List

from operations.operation import Extractor


class GetSpecialChars(Extractor):
    """Extracts the used special char (sequences)."""

    def op_name() -> str: return "get_sc"

    SPECIAL_CHARACTERS_REGEXP = \
        "[<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-]+"
    
    def __init__(self):
        self._re_special_chars = \
            re.compile(self.SPECIAL_CHARACTERS_REGEXP)

    def process(self, entry: str) -> List[str]:
        entries = self._re_special_chars.findall(entry)
        # entries = [
        #     i.group(0) 
        #     for i in self._re_special_chars.finditer(entry)
        # ]
        if len(entries) >= 1:
            return entries
        else:
            return None


GET_SPECIAL_CHARS = GetSpecialChars()
