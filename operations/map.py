from typing import List

from operations.operation import Transformer
from common import escape


class Map(Transformer):
    """ Maps a given character to several alternatives.
    """

    def __init__(self, source_char : str, target_chars : str):
        if not set(source_char).isdisjoint(set(target_chars)):
            raise ValueError(f"useless identity mapping {source_char} [{target_chars}]")

        self.source_char = source_char
        self.raw_target_chars = target_chars
        self.target_chars = set(target_chars) 
        return

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
        target_chars = escape(self.raw_target_chars)
        return f"map {source_char} [{target_chars}]"

