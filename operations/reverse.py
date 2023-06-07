from dj_ops import PerEntryTransformer


class Reverse(PerEntryTransformer):
    """ Reverses a given string.
    """

    def op_name() -> str: return "reverse"

    def process(self, entry: str) -> list[str]:
        new_entry = entry[::-1]
        if new_entry == entry:
            return None
        else:
            return [new_entry]


REVERSE = Reverse()
