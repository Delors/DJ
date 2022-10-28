from typing import List

from operations.operation import Operation


class DeduplicateReversed(Operation):
    """
    Identifies entries where the second part of an entry is the 
    duplication of the first part, but reversed. E.g., "testtset".
    """
   
    def is_extractor(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        length = len(entry)
        if  length % 2 == 1:
            return None

        first_half = entry[0:length//2]    
        second_half = entry[-length//2:][::-1]    
        if first_half == second_half:
            return [first_half]
        else:
            return None

    def __str__(self):
        return "deduplicate_reversed"

DEDUPLICATE_REVERSED = DeduplicateReversed() 