from dj_ops import PerEntryTransformer


class SwapCase(PerEntryTransformer):
    """ Swaps the case of every character.
    """

    def op_name() -> str: return "swapcase"

    def process(self, entry: str) -> list[str]:
        title = entry.swapcase()
        if title != entry:
            return [title]
        else:
            return None


SWAPCASE = SwapCase()
