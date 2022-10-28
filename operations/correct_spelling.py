from typing import List

from Levenshtein import distance

from operations.operation import Operation
from common import dictionaries


class CorrectSpelling(Operation):
    """
    Tries to correct the spelling of an entry by using Nuspell.
    Here, we only consider misspellings with at most one typing
    mistake.
    The costs of this operation depends on the number
    of installed dictionaries, however, with a large set of
    dictionaries, the costs can be very(!) high.
    """

    FILTER_CORRECTIONS_WITH_SPACE = True
    """
    Sometimes the correction of a word can lead to two words. 
    If this setting is set to true, such "corrections" are ignored.
    """

    def __init__(self):
        return

    def is_transformer(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        lentry = entry.lower()
        words = []
        for d in dictionaries.values():
            for c in d.suggest(entry):
                edit_distance = distance(entry,c)
                if edit_distance == 0:
                    # This indicates that "correct spelling" was used 
                    # on well defined terms.
                    return []
                elif edit_distance == 1:
                    if c.lower() == lentry:
                        # "Just" the capitalization was incorrect;
                        # we don't want to report other words.
                        return [c]
                    elif self.FILTER_CORRECTIONS_WITH_SPACE and \
                         c.find(" ") != -1:
                        pass
                    else:
                        words.append(c)
        if len(words) == 0:
            return None    
        else:
            return words

    def __str__(self):
        return "correct_spelling"

CORRECT_SPELLING = CorrectSpelling()
