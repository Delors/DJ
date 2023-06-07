from dj_ops import PerEntryTransformer


class RemoveWS(PerEntryTransformer):
    """ Removes all whitespace.

        See `remove` for a more general variant.
    """

    def op_name() -> str: return "remove_ws"

    def process(self, entry: str) -> list[str]:
        split_entries = entry.split()
        if len(split_entries) == 0:
            # The entry consisted only of WS
            return []
        elif len(split_entries) == 1:
            return None
        else:
            return ["".join(split_entries)]


REMOVE_WS = RemoveWS()
