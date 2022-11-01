from typing import List

from operations.operation import Transformer


class Capitalize(Transformer):
    """Capitalizes a given entry."""

    def process(self, entry: str) -> List[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return None

    def __str__(self):
        return "capitalize"

CAPITALIZE = Capitalize()
