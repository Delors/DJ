from typing import List

from operations.operation import Transformer


class FoldWhitespace(Transformer):
    """Folds multiple whitespace (spaces and tabs) to one space."""

    def process(self, entry: str) -> List[str]:
        last_entry = ""
        folded_entry = entry
        while folded_entry != last_entry:
            last_entry = folded_entry
            folded_entry = folded_entry\
                .replace("  "," ")\
                .replace("\t"," ") # May result in 2 or 3 subsequent spaces
        if entry != folded_entry:
            return [folded_entry]
        else:
            return None

    def __str__(self):
        return "fold_ws"

FOLD_WHITESPACE = FoldWhitespace()