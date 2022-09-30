from typing import List

from Levenshtein import distance

from operations.operation import Operation
from common import dictionaries


class CorrectSpelling(Operation):
    """
    Tries to correct the spelling of an entry by using Hunspell.
    Here, we only consider misspellings with at most one typing
    mistake.
    The costs of this operation depends on the number
    of installed dictionaries.
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
                # If we have a plural word the spellchecker may
                # propose to split up the trainling "s". We don't
                # want that and therefore filter proposals which
                # contain spaces.
                if distance(entry,c) == 1 and c.find(" ") == -1:
                    if c.lower() == lentry:
                        # "just" the capitalization was incorrect;
                        # we don't want to report other words.
                        return [c]
                    else:
                        words.append(c)
        if len(words) == 0:
            return None    
        else:
            return words

    def __str__(self):
        return "correct_spelling"

CORRECT_SPELLING = CorrectSpelling()