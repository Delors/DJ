from typing import List

from operations.operation import Operation


class Capitalize(Operation):
    """Capitalizes a given entry."""

    def is_transformer(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return None

    def __str__(self):
        return "capitalize"

CAPITALIZE = Capitalize()
