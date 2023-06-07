import re

from dj_ops import PerEntryTransformer


class RemoveNO(PerEntryTransformer):
    """ Removes all numbers from an entry. 
    """

    def op_name() -> str: return "remove_no"

    NO_NUMBERS_REGEXP = "[^0-9]+"

    def __init__(self):
        self._re_no_numbers = re.compile(self.NO_NUMBERS_REGEXP)

    def process(self, entry: str) -> list[str]:
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
