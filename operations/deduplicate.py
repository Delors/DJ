from typing import List

from dj_ast import Extractor


class Deduplicate(Extractor):
    """
    Transforms entries where the second half is a duplication 
    of the first half.
    
    E.g. "TestTest" will be transformed to "Test".
    """

    def op_name() -> str: return "deduplicate"

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


DEDUPLICATE = Deduplicate() 