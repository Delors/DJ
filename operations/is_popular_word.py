from dj_ops import PerEntryFilter
from common import get_nlp_vocab


class IsPopularWord(PerEntryFilter):
    """ Checks if a word is a word that is used on twitter or in 
        google news. In case of twitter, the given term is always lowered
        and then tested, because the twitter model only uses lower case
        entries. In case of google the term is taken as is. However,
        it may be necessary/meaningful to first correct the spelling.
        Otherwise, proper nouns may not be correctly identified. 

        This test has very high initialization costs on _first_ usage!
    """

    def op_name() -> str: return "is_popular_word"

    def __init__(self):
        self._twitter_vocab = None
        self._google_vocab = None
        return

    def process(self, entry: str) -> list[str]:
        if not self._twitter_vocab:
            self._twitter_vocab = get_nlp_vocab(
                "twitter", self.td_unit.verbose)
        if not self._google_vocab:
            self._google_vocab = get_nlp_vocab("google", self.td_unit.verbose)

        lentry = entry.lower()

        # NOTE: the twitter model only contains lower case entries!
        # NOTE: in case of the google model it may make sense to check
        #       both capitalizations as a given "password" may use
        #       small letters, even though it is a proper noun
        if self._twitter_vocab.get(lentry) or \
                self._google_vocab.get(entry):
            return [entry]
        if lentry != entry and self._google_vocab.get(lentry):
            return [entry]
        centry = entry.capitalize()
        if centry != entry and self._google_vocab.get(centry):
            return [entry]

        return []


IS_POPULAR_WORD = IsPopularWord()
