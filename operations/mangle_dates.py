import re


from dj_ops import PerEntryTransformer, TDUnit, ASTNode
from common import InitializationFailed


class MangleDates(PerEntryTransformer):
    """ Tries to identify numbers which are dates and then creates various
        representations for the respective date.

        Currently, we try to identify 1st german and then 2nd english dates.
    """

    _re_german_date = \
        re.compile("[^0-9]*([0-9]{1,2})\.?([0-9]{1,2})\.?(19|20)?([0-9]{2})")
    
    _re_english_date = \
        re.compile(
            "[^0-9]*([0-9]{1,2})[/-]?([0-9]{1,2})[/-]?(19|20)?([0-9]{2})")

    def op_name() -> str: return "mangle_dates"

    START_YEAR_20TH = 75
    """Start year in the 20th century; i.e. 19XX."""

    END_YEAR_21ST = 25
    """End year in the 21th century; i.e. 20XX."""

    PRINT_SINGLE_DIGIT_DAYS = True

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.END_YEAR_21ST >= self.START_YEAR_20TH:
            raise InitializationFailed(
                f"{self}: 19{self.START_YEAR_20TH} has to be < 20{self.END_YEAR_21ST}"
            )

    def process(self, entry: str) -> list[str]:
        r = MangleDates._re_german_date.match(entry)
        if r:
            (d, m, c, y) = r.groups()
        else:
            r = MangleDates._re_english_date.match(entry)
            if r:
                (m, d, c, y) = r.groups()

        if not r:
            return None

        """ Currently we only accept dates between 19START_YEAR and 20ENDYEAR.
            The test ist not extremely precise, but should be acceptable for
            our purposes.
        """
        if int(d) > 31 or int(d) == 0 or \
            int(m) > 12 or int(m) == 0 or \
            (int(y) > self.END_YEAR_21ST and
                int(y) < self.START_YEAR_20TH) or \
                (c and (c == 19 or c == 20)):
            # We have to return "None", because we don't consider the
            # current number to be a date!
            return None

        mangled_dates = [d+m+y, y]
        if c:
            mangled_dates.append(d+m+c+y)
            mangled_dates.append(c+y)
        else:
            if int(y) <= 25:
                mangled_dates.append("20"+y)
            else:
                mangled_dates.append("19"+y)

        if (len(d) == 1 or len(m) == 1) and MangleDates.PRINT_SINGLE_DIGIT_DAYS:
            mangled_dates.append(d+m+y)

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

