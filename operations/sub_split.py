from common import escape
from dj_ops import PerEntryTransformer


class SubSplit(PerEntryTransformer):
    """ Splits up an entry using the given split_char as a separator
        creating all possible sub splits, keeping the order.
        E.g. "abc-def-ghi" with "-" as the split char would create:
            abc-def
            def-ghi
            abc-ghi
    """

    def op_name() -> str: return "sub_split"

    def __init__(self, split_char: str):
        self.split_char = split_char

    def __str__(self):
        return f'{SubSplit.op_name()} "{escape(self.split_char)}"'

    def process(self, entry: str) -> list[str]:
        all_segments = entry.split(self.split_char)

        all_segments_count = len(all_segments)
        # Recall that, when the split char appears at least once,
        # we will have at least two segments; even when it appears at
        # the start or end.
        if all_segments_count == 1:
            return None

        segments = list(filter(lambda e: len(e) > 0, all_segments))
        segments_count = len(segments)
        if segments_count == 0:
            # the entry just consisted of the split character
            return []

        entries = []

        def collect(current: str, remaining: list[str], take: int):
            if take == 0:
                entries.append(current)
                return
            if len(remaining) == 0 or take > len(remaining):
                return

            collect(current + remaining[0], remaining[1:], take-1)
            collect(current, remaining[1:], take)

        for i in range(1, segments_count):
            collect("", segments, i)

        entries.extend(segments)
        return entries
