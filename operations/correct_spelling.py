from typing import List

from Levenshtein import distance as levenshtein_distance
from jellyfish import damerau_levenshtein_distance

from dj_ast import Transformer
from common import dictionaries


class CorrectSpelling(Transformer):
    """
    Tries to correct the spelling of an entry by using Nuspell.
    Here, we only consider misspellings with at most one typing
    mistake.
    The costs of this operation depends on the number
    of installed dictionaries, however, even with a single 
    dictionary the costs can already be very(!) high.
    """

    USE_DAMERAU_LEVENSHTEIN = True

    FILTER_CORRECTIONS_WITH_SPACE = True
    """
    Sometimes the correction of a word can lead to two words (e.g., 
    "houseold" > ["household", "house old"]). 
    If this setting is set to true, such "corrections" are ignored.
    """

    MAX_EDIT_DISTANCE = 1

    def op_name() -> str: return "correct_spelling"

    def process(self, entry: str) -> List[str]:
        """
        Processes a given entry and tries to fix spelling mistakes.
        Compared to classical spell-checking we implement a more
        advanced handling regarding the usage of upper letters.
        """
        case_folded_entry = entry.lower()
        words = set()
        for d in dictionaries.values():
            for s in d.suggest(entry):
                if self.USE_DAMERAU_LEVENSHTEIN:
                    edit_distance = damerau_levenshtein_distance(entry, s)
                else:
                    edit_distance = levenshtein_distance(entry, s)

                if edit_distance == 0:
                    # The word was correct...
                    return []
                elif case_folded_entry == s.lower():
                    # We (always) accept greater edit distances, but if and
                    # only if it is due to capitalization issues...
                    return [s]
                elif edit_distance <= CorrectSpelling.MAX_EDIT_DISTANCE:
                    if self.FILTER_CORRECTIONS_WITH_SPACE and \
                            s.find(" ") != -1:
                        pass
                    else:
                        words.add(s)

        if len(words) == 0:
            return None
        else:
            return list(words)


CORRECT_SPELLING = CorrectSpelling()
