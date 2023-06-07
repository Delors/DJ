from dj_ops import PerEntryFilter


class IsSC(PerEntryFilter):
    """ Identifies entries which only consist of the specified special chars.
    """

    def op_name() -> str: return "is_sc"

    SPECIAL_CHARS = set("^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()[]{}\\-")

    def process(self, entry: str) -> list[str]:
        if any(e for e in entry if e not in self.SPECIAL_CHARS):
            return []
        else:
            return [entry]
