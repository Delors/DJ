import re
from typing import List

from dj_ast import Extractor


class GetNO(Extractor):
    """Extracts all numbers."""

    def op_name() -> str: return "get_no"

    _re_numbers = re.compile("[0-9]+")

    def process(self, entry: str) -> List[str]:
        entries = GetNO._re_numbers.findall(entry)
        if len(entries) >= 1:
            return entries
        else:
            return None


GET_NO = GetNO()
