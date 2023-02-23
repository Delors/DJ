# -*- coding: utf-8 -*-
from typing import List

from dj_ast import ASTNode, TDUnit, Filter

KEYBOARD_DE = {
    "HORIZONTAL_NO_SHIFT": {
        "^": ["1", ""],
        "1": ["^", "2"],
        "2": ["1", "3"],
        "3": ["2", "4"],
        "4": ["3", "5"],
        "5": ["4", "6"],
        "6": ["5", "7"],
        "7": ["6", "8"],
        "8": ["7", "9"],
        "9": ["8", "0"],
        "0": ["9", "ß"],
        "ß": ["0", "'"],
        "'": ["ß"],
        "q": ["w"],
        "w": ["q", "e"],
        "e": ["w", "r"],
        "r": ["e", "t"],
        "t": ["r", "z"],
        "z": ["t", "u"],
        "u": ["z", "i"],
        "i": ["u", "o"],
        "o": ["i", "p"],
        "p": ["o", "ü"],
        "ü": ["p", "+"],
        "+": ["ü"],
        "a": ["s"],
        "s": ["a", "d"],
        "d": ["s", "f"],
        "f": ["d", "g"],
        "g": ["f", "h"],
        "h": ["g", "j"],
        "j": ["h", "k"],
        "k": ["j", "l"],
        "l": ["k", "ö"],
        "ö": ["l", "ä"],
        "ä": ["ö", "#"],
        "#": ["ä"],
        "<": ["y"],
        "y": ["<", "x"],
        "x": ["y", "c"],
        "c": ["x", "v"],
        "v": ["c", "b"],
        "b": ["v", "n"],
        "n": ["b", "m"],
        "m": ["n", ","],
        ",": ["m", "."],
        ".": [",", "-"],
        "-": ["."],
    },
    "VERTICAL_NO_SHIFT": {
        "^": [],
        "1": ["q"],
        "2": ["q", "w"],
        "3": ["w", "e"],
        "4": ["e", "r"],
        "5": ["r", "t"],
        "6": ["t", "z"],
        "7": ["z", "u"],
        "8": ["u", "i"],
        "9": ["i", "o"],
        "0": ["o", "p"],
        "ß": ["p", "ü"],
        "'": ["ü", "+"],
        "q": ["1", "2", "a"],
        "w": ["2", "3", "a", "s"],
        "e": ["3", "4", "s", "d"],
        "r": ["4", "5", "d", "f"],
        "t": ["5", "6", "f", "g"],
        "z": ["6", "7", "g", "h"],
        "u": ["7", "8", "h", "j"],
        "i": ["8", "9", "j", "k"],
        "o": ["9", "0", "k", "l"],
        "p": ["0", "ß", "l", "ö"],
        "ü": ["ß", "'", "ö", "ä"],
        "+": ["'", "ä", "#"],
        "a": ["q", "w", "y"],
        "s": ["w", "e", "y", "x"],
        "d": ["e", "r", "x", "c"],
        "f": ["r", "t", "c", "v"],
        "g": ["t", "z", "v", "b"],
        "h": ["z", "u", "b", "n"],
        "j": ["u", "i", "n", "m"],
        "k": ["i", "o", "m", ","],
        "l": ["o", "p", ",", "."],
        "ö": ["p", "ü", ".", "-"],
        "ä": ["ü", "+", "-"],
        "#": ["+"],
        "<": ["a"],
        "y": ["a", "s"],
        "x": ["s", "d"],
        "c": ["d", "f"],
        "v": ["f", "g"],
        "b": ["g", "h"],
        "n": ["h", "j"],
        "m": ["j", "k"],
        ",": ["k", "l"],
        ".": ["l", "ö"],
        "-": ["ö", "ä"],
    }
}

PIN_PAD = {
    "ADJACENT": {
        "1": ["2", "4", "5"],
        "2": ["1", "3", "4", "5", "6"],
        "3": ["2", "5", "6"],
        "4": ["1", "2", "5", "8", "7"],
        "5": ["1", "2", "3", "4", "6", "7", "8", "9"],
        "6": ["2", "3", "5", "8", "9"],
        "7": ["4", "5", "8", "0"],
        "8": ["4", "5", "6", "7", "9", "0"],
        "9": ["5", "6", "8", "0"],
        "0": ["7", "8", "9"],
    }
}

# TODO Make keyboard configuration configurable by putting it into a python file which - when specified - registers itself with the set of keyboards...


class IsWalk(Filter):
    """ Identifies so-called keyboard/pin-pad walks which have at least MIN_WALK_LENGTH
        characters.

        We make the assumption that every sub part of a keyboard walk has 
        to have at least MIN_SUB_WALK_LENGTH elements. I.e., this allows 
        us to identify walks such as "qwerasdf".
    """

    def op_name() -> str: return "is_walk"

    # We create a copy of these "global" variables at instantiation time
    # to facilitate testing the "IsWalk" filter.
    LAYOUT = "KEYBOARD_DE"
    # +inf has to be used if the walk has to go up to the full length of the entry
    MIN_SUB_WALK_LENGTH = 3.0
    MIN_WALK_LENGTH = 3.0  # with 3.0 "just" two adjacent characters are not enough

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self._keyboard_layout = globals()[IsWalk.LAYOUT]
        self._min_walk_length = IsWalk.MIN_WALK_LENGTH
        self._min_sub_walk_length = IsWalk.MIN_SUB_WALK_LENGTH

    def is_filter(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if len(entry) < self._min_walk_length:
            return []

        last_e = entry[0]
        current_length = 1
        for e in entry[1:]:
            current_length += 1
            found = False
            for adjacent in (dir for dir in self._keyboard_layout.values()):
                a = adjacent.get(last_e)
                if a is None:
                    # we found a character that is not in the keyboard definition
                    return []
                if e in a:
                    found = True
                    break

            if not found:
                if current_length <= self._min_sub_walk_length:
                    return []
                else:
                    current_length = 1
            last_e = e

        return [entry]
