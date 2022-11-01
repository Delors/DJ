import re
from typing import List

from operations.operation import Transformer


class Reverse(Transformer):
    """ Reverses a given string.
    """

    def process(self, entry: str) -> List[str]:
        new_entry = entry[::-1]
        if new_entry == entry:
            return None
        else:
            return [new_entry]

    def __str__(self):
        return "reverse"

REVERSE = Reverse()