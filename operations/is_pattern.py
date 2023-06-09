from dj_ops import PerEntryFilter


class IsPattern(PerEntryFilter):
    """ Identifies repetitions of 
         - a single character 
         - a pair of characters
         - three characters
        E.g., "aaaaa" or "qpqpqp" are identified as patterns.
    """

    def op_name() -> str: return "is_pattern"

    def process(self, entry: str) -> list[str]:
        length = len(entry)
        if length < 2:
            return []

        first_char = entry[0]
        if all(first_char == c for c in entry[1:]):
            return [entry]

        second_char = entry[1]
        if first_char == second_char or length == 2:
            # well... given the previous test it is obviously not a 
            # pattern that is based on the repetition of two different 
            # characters
            return []

        if length % 2 == 0 and entry == entry[0:2]*(length//2):
            return [entry]

        if length < 6 or length % 3 != 0:
            return []
        third_char = entry[2]
        if (
                third_char != first_char or
                third_char != second_char or
                second_char != first_char
            ) and \
                entry == entry[0:3]*(length//3):
            return [entry]
        else:
            return []


IS_PATTERN = IsPattern()
