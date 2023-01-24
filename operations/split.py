from typing import List

from dj_ast import Transformer
from common import escape


class Split(Transformer):
    """ Splits up an entry using the given split_char as a separator.
    """

    def op_name() -> str: return "split"

    def __init__(self, split_char: str):
        self.split_char = split_char

    def process(self, entry: str) -> List[str]:
        assert len(entry) > 0

        all_segments = entry.split(self.split_char)
        # "all_segments" will have at least two elements
        # if a split char is found.
        if len(all_segments) == 1:
            return None

        segments = list(filter(lambda e: len(e) > 0, all_segments))
        return segments

    def __str__(self):
        return f'{Split.op_name()} "{escape(self.split_char)}"'
