import re

from dj_ops import PerEntryExtractor


class GetNO(PerEntryExtractor):
    """ Extracts all numbers. """

    _re_numbers = re.compile("[0-9]+")


    def op_name() -> str: return "get_no"

    def process(self, entry: str) -> list[str]:
        entries = GetNO._re_numbers.findall(entry)
        if len(entries) >= 1:
            return entries
        else:
            return None


GET_NO = GetNO()
