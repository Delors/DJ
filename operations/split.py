from typing import List

from operations.operation import Transformer
from common import escape,unescape


class Split(Transformer):
    """ Splits up an entry using the given split_char as a separator.
    """

    def __init__(self, split_char : str):
        self.split_char = split_char
        return

    def process(self, entry: str) -> List[str]:
        assert len(entry) > 0

        all_segments = entry.split(self.split_char)
        # "all_segments" will have at least two elements
        # if a split char is found.
        if len(all_segments) == 1:
            return None
                
        segments = list(filter(lambda e: len(e) > 0, all_segments))
        return segments

    def __str__ (self):
        split_char_def = escape(self.split_char)
        return f"split {split_char_def}"         

