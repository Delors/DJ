import re
from typing import List

from dj_ast import Transformer


class Reverse(Transformer):
    """ Reverses a given string.
    """

    def op_name() -> str: return "reverse"

    def process(self, entry: str) -> List[str]:
        new_entry = entry[::-1]
        if new_entry == entry:
            return None
        else:
            return [new_entry]

REVERSE = Reverse()