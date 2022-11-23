from typing import List

from operations.operation import Filter


class IsPattern(Filter):
    """ Identifies repetitions of a single character or a pair of characters.
        E.g., "aaaaa" or "qpqpqp" are identified as patterns.
    """

    def op_name() -> str: return "is_pattern"

    def process(self, entry: str) -> List[str]:
        length = len(entry)
        if length <= 2:
            return None

        first_char = entry[0]
        if all(first_char == c for c in entry[1:]):
            return [entry]
        
        second_char = entry[1]
        if first_char == second_char or length %2 != 0 or length == 2:
            # well... given the previous test it is obviously not a pattern
            # that is based on the repetition of two different characters
            return []

        if entry == entry[0:2]*(length//2):
            return [entry]
        else:
            return []
              

IS_PATTERN = IsPattern()