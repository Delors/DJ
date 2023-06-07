from dj_ops import PerEntryTransformer


class StripWS(PerEntryTransformer):
    """ Removes leading and trailing whitespace.

        See also: `strip` for a more general strip command.
    """

    def op_name() -> str: return "strip_ws"

    def process(self, entry: str) -> list[str]:
        stripped_entry = entry.strip()
        if stripped_entry is entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of WS
            return []
        else:  # stripped_entry != entry and len(entry) > 0
            return [stripped_entry]


STRIP_WS = StripWS()
