from itertools import groupby

from dj_ast import Filter


class IListUnique(Filter):
    """ Reduces the list of intermediate entries to a list; i.e.,
        duplicates are removed. The order is maintained - except of
        the removal of duplicates.

        Usage scenarios:
         - peformance optimization
         - semantic minimization
    """

    def op_name() -> str: return "ilist_unique"

    def process_entries(self, entries: list[str]) -> list[str]:
        seen_entries = set()
        new_entries = []
        for e in entries:
            if e not in seen_entries:
                seen_entries.add(e)
                new_entries.append(e)
        return new_entries

ISET_UNIQUE = IListUnique()