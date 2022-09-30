from typing import List

from operations.operation import Operation
from common import escape


class Map(Operation):
    """ Maps a given character to several alternatives.
    """

    def __init__(self, source_char : str, target_chars : str):
        self.source_char = source_char
        self.target_chars = set(target_chars) 
        return

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if self.source_char in entry:
            entries = []
            for c in self.target_chars:
                entries.append(entry.replace(self.source_char,c))
            return entries
        else:
            return None         

    def __str__ (self):
        source_char = escape(self.source_char)
        target_chars = escape("".join(self.target_chars))
        return f"maps {source_char} [{target_chars}]"

