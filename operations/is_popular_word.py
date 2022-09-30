from typing import List

from operations.operation import Operation
from common import get_nlp_vocab


class IsPopularWord(Operation):
    # Checks if a word is a word that is used on twitter or in 
    # google news. 
    # This test has very high setup costs!

    def __init__(self):
        self._twitter_vocab = None
        self._google_vocab = None
        return

    def is_filter(self) -> bool: return True
        
    def process(self, entry: str) -> List[str]:        
        if not self._twitter_vocab: 
            self._twitter_vocab = get_nlp_vocab("twitter")
        if not self._google_vocab: 
            self._google_vocab = get_nlp_vocab("google")            
            
        # NOTE: the twitter model only contains lower case entries!
        if not self._twitter_vocab.get(entry.lower()) and \
            not self._google_vocab.get(entry): 
            return []
        else:
            return [entry]

    def __str__(self):
        return "is_popular_word"

IS_POPULAR_WORD = IsPopularWord()