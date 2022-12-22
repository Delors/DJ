from typing import List

from dj_ast import Transformer


class Upper(Transformer):
    """Converts an entry to all upper case."""

    def op_name() -> str: return "upper"

    def process(self, entry: str) -> List[str]:
        upper = entry.upper()
        if upper != entry:
            return [upper]
        else:
            return None
            

UPPER = Upper()   
