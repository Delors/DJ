import re
from typing import List

from dj_ast import Transformer


class RemoveNO(Transformer):
    """Removes all numbers from an entry."""

    def op_name() -> str: return "remove_numbers"

    NO_NUMBERS_REGEXP = "[^0-9]+"

    def __init__(self):
        self._re_no_numbers = re.compile(self.NO_NUMBERS_REGEXP)

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0)
            for i in self._re_no_numbers.finditer(entry)
        ]
        if len(entries) == 0:
            return []
        elif entry != entries[0]:
            return ["".join(entries)]
        else:
            return None


REMOVE_NO = RemoveNO()
