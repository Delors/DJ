from typing import List

from operations.operation import Transformer


class StripWhitespace(Transformer):
    """Removes leading and trailing whitespace."""

    def op_name() -> str: return "strip_ws"

    def process(self, entry: str) -> List[str]:
        stripped_entry = entry.strip()
        if stripped_entry is entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of WS
            return []
        else: # stripped_entry != entry and len(entry) > 0
            return [stripped_entry]


STRIP_WHITESPACE = StripWhitespace()    