from typing import List

from operations.operation import Transformer

class Lower(Transformer):
    """Converts an entry to all lower case."""

    def process(self, entry: str) -> List[str]:
        lower = entry.lower()
        if lower != entry:
            return [lower]
        else:
            return None

    def __str__(self):
        return "lower"    

LOWER = Lower()  