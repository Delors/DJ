from typing import List

from dj_ast import Filter


class IsSC(Filter):
    """ Identifies entries which only consist of certain special chars.
    """

    def op_name() -> str: return "is_sc"

    SPECIAL_CHARS = set("^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()[]{}\\-")

    def process(self, entry: str) -> List[str]:
        if any(e for e in entry if e not in self.SPECIAL_CHARS):
            return []        
        else:
            return [entry]


IS_SC = IsSC()