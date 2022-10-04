import re
from typing import List

from Levenshtein import distance

from operations.operation import Operation
from common import dictionaries

class IsRegularWord(Operation):
    """ Checks if a word is a real word by looking it up in several
        dictionaries.
    """

    _match_words = re.compile("[^\W\d_]+")

    def __init__(self):
        return

    def is_filter(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        try:
            if any(d.spell(entry) for d in dictionaries.values()):
                return [entry]
            else:
                return []
        except:
            pass

    def __str__(self):
        return "is_regular_word"

IS_REGULAR_WORD = IsRegularWord()