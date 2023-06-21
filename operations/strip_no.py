from dj_ops import PerEntryTransformer


class StripNo(PerEntryTransformer):
    """Removes leading and trailing numbers and ascii special chars."""

    def op_name() -> str: return "strip_no"

    def process(self, entry: str) -> list[str]:
        stripped_entry = entry.strip("0123456789")
        if stripped_entry == entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of stripped entries
            return []
        else:  # stripped_entry != entry:
            # The entry is not empty
            return [stripped_entry]

STRIP_NO = StripNo()