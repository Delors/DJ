from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryTransformer
from common import escape,InitializationFailed


class Split(PerEntryTransformer):
    """ Splits up an entry using the given split_char as a separator.
    """

    def op_name() -> str: return "split"

    def __init__(self, split_char: str):
        self.split_char = split_char

    def __str__(self):
        return f'{Split.op_name()} "{escape(self.split_char)}"'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.split_char) == 0:
            raise InitializationFailed(f"{self}: missing split character")
        return self

    def process(self, entry: str) -> list[str]:
        if len(entry) == 0:
            return None

        all_segments = entry.split(self.split_char)
        # "all_segments" will have at least two elements
        # if a split char is found.
        if len(all_segments) == 1:
            return None

        segments = list(filter(lambda e: len(e) > 0, all_segments))
        return segments
