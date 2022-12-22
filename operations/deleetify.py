import itertools
import re
from typing import List, Set

from dj_ast import Transformer

class DeLeetify(Transformer):
    """ Deleetifies an entry by replacing the used numbers with their
        respective characters. E.g., *T3st* is deleetified to _Test_. To avoid
        the creation of irrelevant entries, a spellchecker should be used to test 
        that the deleetified word is a real world. Please note, that using
        a spellchecker directly to deleetify a word will generally not work
        for heavily leetified words, e.g., _T4553_, which might stand for 
        _Tasse_ in German.

        We currently only deleetify words containing
        a, e, i and o.
    """

    def op_name() -> str: return "deleetify"

    """
    mappings = {
            ("0","o"),
            ("3","e"),
            ("4","a"),
            ("1","i")
        }
    """
    """ Currently not used transliterations:
            [("5","s")],
            [("6","g")],
            [("7","t")],
            [("8","b")],
            [("1","l")],
            [("2","r"),("2","z")],
            [("4","h")],
            [("9","p"),("9","g")]"""

    replacements = list(
        itertools.chain.from_iterable(
            itertools.combinations({
                ("0","o"),
                ("1","i"),
                ("3","e"),
                ("4","a")                
            },l) for l in range(1,4)
        )
    )

    # REs to test if we have leetspeak. The REs are based on the assumption that
    # we never have words with more than three subsequent vowles and that the
    # numbers 0,3,4,1 are the only relevant ones.
    # (In reality such words exists; e.g. Aioli !)
    _re_has_at_least_one_seq_with_at_most_three_numbers = \
        re.compile("[^0-9]*[0134]{1,3}([^0-9]|$)")
    _re_has_leetspeak = \
        re.compile(".*[a-zA-Z]")


    def process(self, entry: str) -> List[str]:
        # (See Wikipedia for more details!) We currently only consider
        # the basic visual transliterations related to numbers and
        # we assume that a user only uses one specific transliteration
        # if multiple alternatives exists. I.e., a word such as _Hallo_
        # will either be rewritten as: _4allo_ or _H4llo_ or _H411o_, but 
        # will never be rewritten to _44llo_. In the last case, the mapping is
        # no longer bijective. Additionally, we assume that a user uses
        # at most three transliterations and only transliterates vowels. 
        # The last two decisions are made based on "practical" observations
        # and to keep the computational overhead reasonable.

        # The following tests are just an optimization:
        if  not DeLeetify._re_has_at_least_one_seq_with_at_most_three_numbers.match(entry) or\
            not DeLeetify._re_has_leetspeak.match(entry):
            return None

        # TODO [IMPROVEMENT] First scan for all numbers in the entry and then perform the relevant transformations instead of testing all combinations of transformations.

        deleetified_entries : Set[str] = set()
        for rs in DeLeetify.replacements:            
            deleetified_entry = entry
            for (n,c) in rs:
                deleetified_entry = deleetified_entry.replace(n,c)
            if entry != deleetified_entry:
                deleetified_entries.add(deleetified_entry)
        
        if len(deleetified_entries) == 0:
            return None
        else:
            return list(deleetified_entries)


DELEETIFY = DeLeetify() 