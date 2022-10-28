from typing import List

from operations.operation import Operation


class Detriplicate(Operation):
    """
    Transforms entries where the second and third thirds are a 
    repetition of the first third.
    
    E.g. "TestTestTest" will be transformed to "Test".
    """
   
    def is_extractor(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        length = len(entry)
        if  length % 3 != 0:
            return None
        frag_length = length//3
        first_third = entry[0:frag_length]    
        second_third = entry[frag_length:2*frag_length]    
        third_third = entry[-frag_length:]    
        if first_third == second_third and second_third == third_third:
            return [first_third]
        else:
            return None

    def __str__(self):
        return "detriplicate"

DETRIPLICATE = Detriplicate() 