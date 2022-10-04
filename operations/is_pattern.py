from typing import List

from operations.operation import Operation


class IsPattern(Operation):
    """Identifies repetitions of a single character or a pair of characters.
    """

    def is_filter(self) -> bool: 
        return True

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
              

    def __str__(self):
        return "is_pattern"   

IS_PATTERN = IsPattern()