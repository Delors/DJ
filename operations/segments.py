from typing import List

from common import InitializationFailed
from dj_ast import Extractor, TDUnit, ASTNode


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

    def __init__(self, min_length: int, max_length: int):
        self.min_length = min_length
        self.max_length = max_length

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.max_length < self.min_length:
            msg = f"{self}: MAX_LENGTH < MIN_LENGTH"
            raise InitializationFailed(msg)

        if self.min_length < 1:
            msg = f"{self}: MIN_LENGTH has to be equal or larger than 1"
            raise InitializationFailed(msg)

        return

    def process(self, entry: str) -> List[str]:
        if len(entry) < self.min_length:
            return None

        segments = []
        for l in range(self.max_length, self.min_length-1, -1):
            for i in range(0, len(entry)-l+1):
                segments.append(entry[i:i+l])

        return segments

    def __str__(self):
        return f"{Segments.op_name()} {self.max_length}"
