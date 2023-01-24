from typing import List

from common import escape
from dj_ast import Transformer


class SubSplit(Transformer):
    """ Splits up an entry using the given split_char as a separator
        creating all possible sub splits, keeping the order.
        E.g. Abc-def-ghi with "-" as the split char would create:
            Abc-def
            def-ghi
            Abc-ghi
    """

    def op_name() -> str: return "sub_splits"

    def __init__(self, split_char: str):
        self.split_char = split_char
        return

    def process(self, entry: str) -> List[str]:
        assert len(entry) > 0

        all_segments = entry.split(self.split_char)

        all_segments_count = len(all_segments)
        # Recall that, when the split char appears at least once,
        # we will have at least two segments; even it appears at
        # the start or end.
        if all_segments_count == 1:
            return None

        segments = filter(lambda e: len(e) > 0, all_segments)
        segments_count = len(segments)
        if segments_count == 0:
            # the entry just consisted of the split character
            return []

        entries = []
        for i in range(2, segments_count):
            entries.append(self.split_char.join(segments[0:i]))
        for i in range(1, segments_count-1):
            entries.append(self.split_char.join(segments[i:segments_count]))

        entries.extend(segments)
        return entries

    def __str__(self):
        split_char_def = self.split_char\
            .replace(' ', "\\s")\
            .replace('\t', "\\t")
        return f'{SubSplit.op_name()} "{escape(split_char_def)}"'
