import re
from typing import List

from operations.operation import Transformer


class MangleDates(Transformer):
    """ Tries to identify numbers which are dates and then creates various
        representations for the respective date.

        Currently, we try to identify 1st german and then 2nd english dates.
    """

    START_YEAR_20TH = 75
    """Start year in the 20th century; i.e. 19XX."""

    END_YEAR_21ST = 25    
    """End year in the 21th century; i.e. 20XX."""

    _re_german_date = \
        re.compile("[^0-9]*([0-9]{1,2})\.?([0-9]{1,2})\.?(19|20)?([0-9]{2})")
    _re_english_date = \
        re.compile("[^0-9]*([0-9]{1,2})[/-]?([0-9]{1,2})[/-]?(19|20)?([0-9]{2})")    

    def __init__(self): 
        if self.END_YEAR_21ST >= self.START_YEAR_20TH: 
            raise ValueError(
                f"19{self.START_YEAR_20TH} has to be < 20{self.END_YEAR_21ST}"
            )
        pass

    def process(self, entry: str) -> List[str]:
        r = MangleDates._re_german_date.match(entry)
        if r:
            (d,m,c,y) = r.groups()
        else:
            r = MangleDates._re_english_date.match(entry)
            if r:
                (m,d,c,y) = r.groups()

        if not r:    
            return None

        """Currently we only accept dates between 19START_YEAR and 20ENDYEAR.
            The test ist not extremely precise, but should be acceptable for
            our purposes.
        """
        if  int(d) > 31 or int(d) == 0 or \
            int(m) > 12 or int(m) == 0 or \
            (   int(y) > self.END_YEAR_21ST and \
                int(y) < self.START_YEAR_20TH) or \
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