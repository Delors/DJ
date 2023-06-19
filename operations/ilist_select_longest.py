from itertools import groupby

from dj_ast import Filter


class IListSelectLongest(Filter):
    """ Among the set of entries that were derived from a single dictionary
        entry (e.g., due to splitting up the entries, finding related words, 
        etc.), those entries are selected where each entry is not part
        of another entry; the order is maintained!
    """

    def op_name() -> str: return "ilist_select_longest"

    def process_entries(self, entries: list[str]) -> list[str]:
        # Precondition: entries is a list of unique entries!
        if len(entries) == 1:
            return entries

        longest_entries = []
        for e in entries:
            if not longest_entries:
                longest_entries = [e]
                continue

            if not any([True for le in longest_entries if e in le]):
                # e is not in any previously identified word...
                replaced = False
                for i in range(0,len(longest_entries)):
                    if longest_entries[i] in e:
                        # e is longer than a previous word...
                        new_longest_entries = longest_entries[0:i]
                        new_longest_entries.extend(longest_entries[i+1:len(longest_entries)])
                        new_longest_entries.append(e)
                        longest_entries = new_longest_entries
                        replaced = True
                        break
                if not replaced:
                    longest_entries.append(e)

        return longest_entries



ILIST_SELECT_LONGEST = IListSelectLongest()