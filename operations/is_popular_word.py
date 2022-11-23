from typing import List

from operations.operation import Filter
from common import get_nlp_vocab


class IsPopularWord(Filter):
    """ Checks if a word is a word that is used on twitter or in 
        google news. In case of twitter, the given term is always lowered
        and then tested, because the twitter model only uses lower case
        entries. In case of google the term is taken as is. However,
        it may be necessary/meaning ful to first correct the spelling.
        Otherwise, proper nouns may not be correctly identified. 

        This test has very high initialization costs on _first_ usage!
    """

    def op_name() -> str: return "is_popular_word"

    def __init__(self):
        self._twitter_vocab = None
        self._google_vocab = None
        return
        
    def process(self, entry: str) -> List[str]:        
        if not self._twitter_vocab: 
            self._twitter_vocab = get_nlp_vocab("twitter")
        if not self._google_vocab: 
            self._google_vocab = get_nlp_vocab("google")            

        lentry = entry.lower()    

        # NOTE: the twitter model only contains lower case entries!
        # NOTE: in case of the google model it may make sense to check
        #       both capitalizations as a given "password" may use 
        #       small letters, even though it is a proper noun
        if not self._twitter_vocab.get(lentry) and \
            not self._google_vocab.get(entry):
            return []
        # centry = entry.capitalize() 
        # if centry != entry and not self._google_vocab.get(entry):
        #     return []    
        else:
            return [entry]


IS_POPULAR_WORD = IsPopularWord()