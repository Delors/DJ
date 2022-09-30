from typing import List

from operations.operation import Operation


class Upper(Operation):
    """Converts an entry to all upper case."""

    def is_transformer(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        upper = entry.upper()
        if upper != entry:
            return [upper]
        else:
            return None

    def __str__(self):
        return "upper"    

UPPER = Upper()   
