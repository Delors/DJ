from typing import List

from dj_ast import Transformer


class Lower(Transformer):
    """Converts an entry to all lower case."""

    def op_name() -> str: return "lower"

    def process(self, entry: str) -> List[str]:
        lower = entry.lower()
        if lower != entry:
            return [lower]
        else:
            return None


LOWER = Lower()
