from typing import List

from operations.operation import Operation


class Deduplicate(Operation):
    # If an entry is a duplication of a sequence, the first part
    # will be returned. E.g. "TestTest" will be transformed to 
    # "Test"
   
    def is_extractor(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        length = len(entry)
        if  length % 2 == 1:
            return None

        first_half = entry[0:length//2]    
        second_half = entry[-length//2:]    
        if first_half == second_half:
            return [first_half]
        else:
            return None

    def __str__(self):
        return "deduplicate"

DEDUPLICATE = Deduplicate() 