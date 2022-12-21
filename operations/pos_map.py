from typing import List

from operations.operation import Transformer
from common import escape


class PosMap(Transformer):
    """ Maps each character at every position to a character from the given set of characters.
        For example:
        Given the operation:
            pos_map [ab]
        and the dictionary entry:
            Test
        PosMap will generate the following output:
            aest
            best
            Tast
            Tbst
            Teat
            Tebt
            Tesa
            Tesb
    """

    def op_name() -> str: return "pos_map"

    def __init__(self, target_chars : str):        
        if (len(target_chars) == 0):
            raise ValueError("pos_map's target chars must not be empty")

        self.raw_target_chars = target_chars
        self.target_chars = set(target_chars) 
        return

    def process(self, entry: str) -> List[str]:
        entries = []
        entry_len = len(entry)
        for i in range(0,entry_len):
            for c in self.target_chars:
                entries.append(entry[0:i]+c+entry[i+1:entry_len])

        return entries
        

    def __str__ (self):
        target_chars = escape(self.raw_target_chars)
        return f"{PosMap.op_name()} [{target_chars}]"

