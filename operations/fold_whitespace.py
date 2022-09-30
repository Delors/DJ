import re
from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from operations.operation import Operation


class FoldWhitespace(Operation):
    """ Folds multiple whitespace (spaces and tabs) to one space."""

    def is_transformer(self) -> bool: return True

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