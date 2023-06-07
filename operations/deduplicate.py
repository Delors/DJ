from dj_ops import PerEntryExtractor


class Deduplicate(PerEntryExtractor):
    """
    Transforms entries where the second half is a duplication 
    of the first half.

    E.g. "TestTest" will be transformed to "Test".
    """

    def op_name() -> str: return "deduplicate"

    def process(self, entry: str) -> list[str]:
        length = len(entry)
        if length % 2 == 1:
            return None

        first_half = entry[0:length//2]
        second_half = entry[-length//2:]
        if first_half == second_half:
            return [first_half]
        else:
            return None

    def derive_rules(self, entry: str) -> list[tuple[str, str]]:
        # Returned value: the first string is the result of the
        #                 operation; the second is the operation
        #                 to regenerate the original string.
        r = self.process(entry)
        if r is not None:
            return [(r[0], "multiply 2")]

        return r


DEDUPLICATE = Deduplicate()
