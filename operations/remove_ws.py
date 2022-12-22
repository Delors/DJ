from typing import List

from dj_ast import Transformer


class RemoveWS(Transformer):
    """Removes all whitespace."""

    def op_name() -> str: return "remove_ws"

    def process(self, entry: str) -> List[str]:
        split_entries = entry.split()
        if len(split_entries) == 0:
            # The entry consisted only of WS
            return []
        elif len(split_entries) == 1:  
            return None
        else:
            return ["".join(split_entries)]


REMOVE_WS = RemoveWS()  