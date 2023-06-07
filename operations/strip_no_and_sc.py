from dj_ops import PerEntryTransformer


class StripNOAndSC(PerEntryTransformer):
    """Removes leading and trailing numbers and ascii special chars."""

    def op_name() -> str: return "strip_numbers_and_sc"

    STRIP_CHARS = "0123456789<>«»“”()[]{}|‘’,;.:_#'+*~@€²³`´^°!\"§$£¥¢%&/=?µ\\- ¡¿•"

    def process(self, entry: str) -> list[str]:

        stripped_entry = entry.strip(self.STRIP_CHARS)
        if stripped_entry == entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of stripped entries
            return []
        else:  # stripped_entry != entry:
            # The entry is not empty
            return [stripped_entry]
