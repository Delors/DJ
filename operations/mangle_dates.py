import re
from typing import List

from operations.operation import Operation


class MangleDates(Operation):
    """ Tries to identify numbers which are dates and then creates various
        representations for the respective date.

        Currently, we try to identify 1st german and then 2nd english dates.
    """

    re_german_date = \
        re.compile("[^0-9]*([0-9]{1,2})\.?([0-9]{1,2})\.?(19|20)?([0-9]{2})")
    re_english_date = \
        re.compile("[^0-9]*([0-9]{1,2})[/-]?([0-9]{1,2})[/-]?(19|20)?([0-9]{2})")    

    def __init__(self): pass

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        r = MangleDates.re_german_date.match(entry)
        if r:
            (d,m,c,y) = r.groups()
        else:
            r = MangleDates.re_english_date.match(entry)
            if r:
                (m,d,c,y) = r.groups()

        if not r:    
            return None

        """Currently we only accept dates between 1975 and 2025.
            The test ist not extremely precise, but should be acceptable for
            our purposes.
        """
        if  int(d) > 31 or int(d) == 0 or \
            int(m) > 12 or int(m) == 0 or \
            (   int(y) > 25 and int(y) < 75) or \
                (c and (c == 19 or c == 20)):
            return []

        mangled_dates = [d+m+y,y]
        if c:
            mangled_dates.append(d+m+c+y)
            mangled_dates.append(c+y)
        else:
            if int(y) <= 25:
                mangled_dates.append("20"+y)
            else:
                mangled_dates.append("19"+y)

        if len(d) == 1:
            if len(m) == 1:
                mangled_dates.append("0"+d+"0"+m+y)
                mangled_dates.append("0"+d+"0"+m)
                mangled_dates.append("0"+m+"0"+d)
            else:
                mangled_dates.append("0"+d+m+y)
                mangled_dates.append("0"+d+m)
                mangled_dates.append(m+"0"+d)
        else:
            if len(m) == 1:
                mangled_dates.append(d+"0"+m+y)
                mangled_dates.append(d+"0"+m)
                mangled_dates.append("0"+m+d)
            else:
                mangled_dates.append(d+m)
                mangled_dates.append(m+d)

        return mangled_dates
            

    def __str__ (self):
        return "mangle_dates"

MANGLE_DATES = MangleDates() 