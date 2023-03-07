from typing import List
from functools import partial
from itertools import groupby

from common import InitializationFailed
from dj_ast import ASTNode, TDUnit, Filter


class SelectLongest(Filter):
    """ Among the set of entries that were derived from a single dictionary
        entry (e.g., due to splitting up the entries, finding related word, 
        etc.), the set of entries is selected where each entry is not part
        of another entry.
    """

    def op_name() -> str: return "select_longest"

    def process_entries(self, entries: List[str]) -> List[str]:
        # Precondition: entries is a list of unique entries!

        # Idea: to minimize the number of string comparisons using the 
        #       "in" operator, we first sort the list in ascending order
        #       w.r.t. the length and then group the list. In the map a
        #       key is the length of the strings found in the values list.
        #       Hence, we do not need to compare strings having the same
        #       length and only have to check for the subset relation 
        #       w.r.t. to those that are already identified as being the
        #       longest ones.

        entries.sort(key=lambda x: -len(x)) # sort longest first
        grouped_entries = groupby(entries,lambda x: len(x))
        current_longest = list(grouped_entries.__next__()[1]) # the list of longest entries
        for (_,next_shorter_entries) in grouped_entries:
            additional_longest = []

            for next_shorter_entry in next_shorter_entries:
                if any([True for cl in current_longest if next_shorter_entry in cl]):
                    continue
                additional_longest.append(next_shorter_entry) 

            current_longest.extend(additional_longest)

        return current_longest

SELECT_LONGEST = SelectLongest()