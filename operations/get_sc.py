import re

from dj_ops import PerEntryExtractor


class GetSC(PerEntryExtractor):
    """ Extracts the used special char (sequences).
        The set can be configured globally.
    """

    def op_name() -> str: return "get_sc"

    SPECIAL_CHARACTERS_REGEXP = \
        "[<>|,;.:_#+*~@€²³^°!\"§$%&/()\[\]{}´`'\\\-]+"

    def __init__(self):
        self._re_special_chars = \
            re.compile(self.SPECIAL_CHARACTERS_REGEXP)

    def process(self, entry: str) -> list[str]:
        entries = self._re_special_chars.findall(entry)
        # entries = [
        #     i.group(0)
        #     for i in self._re_special_chars.finditer(entry)
        # ]
        if len(entries) >= 1:
            return entries
        else:
            return None

