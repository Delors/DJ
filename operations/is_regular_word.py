import re
from typing import List

from Levenshtein import distance

from dj_ast import TDUnit, ASTNode, Filter
from common import dictionaries as all_dictionaries


class IsRegularWord(Filter):
    """ Checks if a word is a _real_ word by looking it up in several
        dictionaries; for that the lower case variant of the entry and
        the capitalized variant is tested. 

        The set of dictionaries that is used is based 
        on those defined in `common.dictionaries`.
    """

    def op_name() -> str: return "is_regular_word"

    DICTIONARIES = ["de","en","nl"]

    def __init__(self) -> None:
        self.dictionaries = []

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        for d in IsRegularWord.DICTIONARIES:
            self.dictionaries.append(all_dictionaries[d])
        return self

    def process(self, entry: str) -> List[str]:
        lentry = entry.lower()
        centry = entry.capitalize()
        try:
            if any((d.spell(lentry) or d.spell(centry)) for d in self.dictionaries):
                return [entry]
            else:
                return []
        except:
            pass
