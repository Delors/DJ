from dj_ops import PerEntryTransformer


class DeduplicateReversed(PerEntryTransformer):
    """
    Identifies entries where the second part of an entry is the 
    duplication of the first part, but reversed. E.g., "testtset".
    """

    def op_name() -> str: return "deduplicate_reversed"

    def process(self, entry: str) -> list[str]:
        length = len(entry)
        if length % 2 == 1:
            if length < 3:
                return None
            # let's check for a pivot element 
            # e.g., in 1234-4321, we have the
            # pivot element "-"
            first_half = entry[0:length//2]
            second_half = entry[-(length-1)//2:][::-1]
        else:
            first_half = entry[0:length//2]
            second_half = entry[-length//2:][::-1]
        if first_half == second_half:
            return [first_half]
        else:
            return None


DEDUPLICATE_REVERSED = DeduplicateReversed()
