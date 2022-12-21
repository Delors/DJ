import re
from typing import List

from Levenshtein import distance

from operations.operation import Filter
from common import dictionaries

class IsRegularWord(Filter):
    """ Checks if a word is a _real_ word by looking it up in several
        dictionaries; for that the lower case variant of the entry and
        the capitalized variant is tested. 
        
        The set of dictionaries that is used is based 
        on those defined in `common.dictionaries`.
    """

    def op_name() -> str: return "is_regular_word"

    def __init__(self):
        return

    def process(self, entry: str) -> List[str]:
        lentry = entry.lower()
        centry = entry.capitalize()
        try:
            if any((d.spell(lentry) or d.spell(centry)) for d in dictionaries.values()):
                return [entry]
            else:
                return []
        except:
            pass


IS_REGULAR_WORD = IsRegularWord()