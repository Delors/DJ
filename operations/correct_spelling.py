from typing import List

from Levenshtein import distance as levenshtein_distance
from jellyfish import damerau_levenshtein_distance

from operations.operation import Transformer
from common import dictionaries


class CorrectSpelling(Transformer):
    """
    Tries to correct the spelling of an entry by using Nuspell.
    Here, we only consider misspellings with at most one typing
    mistake.
    The costs of this operation depends on the number
    of installed dictionaries, however, with a large set of
    dictionaries, the costs can be very(!) high.
    """

    USE_DAMERAU_LEVENSHTEIN = True 

    FILTER_CORRECTIONS_WITH_SPACE = True
    """
    Sometimes the correction of a word can lead to two words. 
    If this setting is set to true, such "corrections" are ignored.
    """

    MAX_EDIT_DISTANCE = 1

    def op_name() -> str: return "correct_spelling"

    def __init__(self):
        return

    def process(self, entry: str) -> List[str]:
        """
        Processes a given entry and tries to fix spelling mistakes.
        Compared to classical spell-checking we implement a more
        advanced handling regarding the usage of upper letters.
        """
        case_folded_entry = entry.casefold 
        words = []
        for d in dictionaries.values():            
            for c in d.suggest(entry):
                if self.USE_DAMERAU_LEVENSHTEIN:
                    edit_distance = damerau_levenshtein_distance(entry,c)
                else:
                    edit_distance = levenshtein_distance(entry,c)

                if edit_distance == 0:
                    return []
                elif edit_distance <= CorrectSpelling.MAX_EDIT_DISTANCE:
                    if self.FILTER_CORRECTIONS_WITH_SPACE and \
                        c.find(" ") != -1:
                        pass
                    else:
                        words.append(c)
                elif case_folded_entry == c.casefold: 
                    # We accept greater edit distances if and only if 
                    # it is due to capitalization issues... 
                    words.append(c)

        """
        lentry = entry.lower()
        tentry_is_entry = None
        if entry.islower() or entry.istitle():
            tentry = entry
            tentry_is_entry = True
        else: 
            tentry = lentry
            tentry_is_entry = False

        if entry == "TeSt": print(f"{lentry} == {tentry} == {entry}")

        words = []
        for d in dictionaries.values():            
            for c in d.suggest(tentry):
                if self.USE_DAMERAU_LEVENSHTEIN:
                    edit_distance = damerau_levenshtein_distance(tentry,c)
                else:
                    edit_distance = levenshtein_distance(tentry,c)

                if entry == "TeSt": print(f" {tentry} => {c} - distance{edit_distance}")    
                if edit_distance == 0:
                    if tentry_is_entry:
                        # The word is not misspelled (w.r.t. the analyzed langs.)
                        return []
                    else:
                        return [c]
                elif c.lower() == lentry:
                    # "Just" the capitalization was incorrect;
                    # we don't want to report other words.
                    return [c]
                elif edit_distance <= CorrectSpelling.MAX_EDIT_DISTANCE:
                    if entry == "TeSt": print(f"c={c}.lower {c.lower()} == {lentry} == {tentry} == {entry}")
                    if self.FILTER_CORRECTIONS_WITH_SPACE and \
                        c.find(" ") != -1:
                        pass
                    else:
                        words.append(c)
        """


        if len(words) == 0:
            return None    
        else:
            return words


CORRECT_SPELLING = CorrectSpelling()
