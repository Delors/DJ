from typing import List

from operations.operation import Transformer


class StripWhitespace(Transformer):
    """Removes leading and trailing whitespace."""

    def process(self, entry: str) -> List[str]:
        stripped_entry = entry.strip()
        if stripped_entry is entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of WS
            return []
        else: # stripped_entry != entry and len(entry) > 0
            return [stripped_entry]

    def __str__(self):
        return "strip_ws"

STRIP_WHITESPACE = StripWhitespace()    