from typing import List

from operations.operation import Transformer


class RemoveWhitespace(Transformer):
    """Removes all whitespace."""

    def process(self, entry: str) -> List[str]:
        split_entries = entry.split()
        if len(split_entries) == 0:
            # The entry consisted only of WS
            return []
        elif len(split_entries) == 1:  
            return None
        else:
            return ["".join(split_entries)]

    def __str__(self):
        return "remove_ws"

REMOVE_WHITESPACE = RemoveWhitespace()  