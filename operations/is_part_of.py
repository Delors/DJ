from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryFilter
from common import InitializationFailed, escape


class IsPartOf(PerEntryFilter):
    """ Tests if a given entry is part of the specified sequence.

        For example "cde" is part of the sequence "abcdefghijklmnopqrstuvwxyz".
    """

    def op_name() -> str: return "is_part_of"

    ENTRY_MIN_LENGTH = 3
    """ Only entries of the given minimum length are checked for being
        a part of the specified sequence.
    """

    MIN_SEQUENCE_LENGTH = 3

    WRAP_AROUND = True

    def __init__(self, sequence: str) -> None:
        self.sequence = sequence

    def __str__(self):
        return f'{IsPartOf.op_name()} "{escape(self.sequence)}"'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.sequence) < 2:
            raise InitializationFailed(
                f"{self}: a sequence has to have at least two characters")
        if IsPartOf.ENTRY_MIN_LENGTH <= 1:
            raise InitializationFailed(
                f"{self}: ENTRY_MIN_LENGTH has to be larger than 1"
            )
        if len(self.sequence) < IsPartOf.ENTRY_MIN_LENGTH:
            raise InitializationFailed(
                f"{self}: the length of the sequence is smaller than ENTRY_MIN_LENGTH"
            )
        if IsPartOf.MIN_SEQUENCE_LENGTH > IsPartOf.ENTRY_MIN_LENGTH:
            raise InitializationFailed(
                f"{self}: MIN_SEQUENCE_LENGTH <= ENTRY_MIN_LENGTH")

    def process(self, entry: str) -> list[str]:
        if len(entry) < IsPartOf.ENTRY_MIN_LENGTH:
            return []

        remaining_entry = entry
        len_sequence = len(self.sequence)
        MIN_SEQ_LEN = IsPartOf.MIN_SEQUENCE_LENGTH
        i = 0  # the index of the next character in the sequence that needs to be  matched AFTER we found a matching character
        while i < len_sequence:
            # 1. let's find a matching character in the sequence for the remaining entry
            s = self.sequence[i]
            i += 1
            if remaining_entry[0] != s:
                continue

            # 2. let's try to match the rest of the remaining entry..
            len_remaining_entry = len(remaining_entry)
            if len_remaining_entry < MIN_SEQ_LEN:
                break

            next_i = i % len(self.sequence)
            if next_i == 0 and not IsPartOf.WRAP_AROUND:
                break

            remaining_chars = len_remaining_entry - 1
            remaining_i = 1
            while remaining_i < len_remaining_entry:
                e = remaining_entry[remaining_i]
                remaining_i += 1
                if self.sequence[next_i] != e:
                    break
                else:
                    remaining_chars -= 1
                    next_i = (next_i+1) % len(self.sequence)
                    if remaining_chars > 0 and next_i == 0 and not IsPartOf.WRAP_AROUND:
                        break
            # 3. check that we have a "reasonable" match
            if remaining_chars == 0:
                return [entry]
            elif remaining_i-1 >= MIN_SEQ_LEN:
                # The last match was long enough, but we are not done yet...
                # 3.1. check if the rest is "long enough"
                if remaining_chars >= MIN_SEQ_LEN:
                    # Update entry ...
                    remaining_entry = remaining_entry[(remaining_i-1):]
                    # Reset i to start again for matching the next part;
                    # this is necessary since we do not wrap around the
                    # initial search in the sequence!
                    i = 0
                # 3.2. check if we can steal something from the current/last match
                elif (remaining_i-1)-(MIN_SEQ_LEN-remaining_chars) >= MIN_SEQ_LEN:
                    # The remaining length is to short, let's try to find a
                    # matching sequence by taking some of the
                    # matched characters and trying to match it again.
                    remaining_entry = remaining_entry[len_remaining_entry-MIN_SEQ_LEN:]
                    i = 0

        return []
