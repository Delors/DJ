from typing import List

from dj_ast import Extractor


class Segments(Extractor):
    """ Returns all segments of a given maxium length and with a given minimum length.

        Example: 
        Started:
            $ ./DJ.py segments 2
        Given:
            abcd
        Result:
            ab
            bc
            cd
            a
            b
            c
            d
        ```
    """
    def op_name() -> str: return "segments"

    MIN_LENGTH = 1
    """Only entries which have the specified min length will be segmented."""

    def __init__(self, max_segment_length : int):
        if max_segment_length < 1:
            raise ValueError(f"MAX_SEGMENT_LENGTH is too small ({max_segment_length})")
        self._max_segment_length = max_segment_length

        if self.MIN_LENGTH < 1:
            raise ValueError(f"MIN_LENGTH has to be equal or larger than 1")

        return

    def process(self, entry: str) -> List[str]:
        if len(entry) < self.MIN_LENGTH:
            return None

        segments = []
        for l in range(self._max_segment_length,self.MIN_LENGTH-1,-1):
            for i in range(0,len(entry)-l+1):
                segments.append(entry[i:i+l])
         
        return segments
            
    def __str__ (self):
        return f"{Segments.op_name()} {self._max_segment_length}"           
 