import re
from typing import List

from dj_ast import Extractor, TDUnit, ASTNode
from common import escape, InitializationFailed


class M(Extractor):
    """ Uses the given regular expressions to extract words.
        E.g. to extract subwords, the regular expression 
        "'[A-Z][a-z]*'" could be used.

        # Example Usage
        `./dj.py 'm "[A-Z][a-z]*" report'`
    """

    def op_name() -> str: return "m"

    def __init__(self, regexp : str) -> None:
        super().__init__()
        self.regexp = regexp

    def init(self, td_unit: TDUnit, parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        try:
            self.m = re.compile(self.regexp)
        except Exception as e:
            raise InitializationFailed(f"invalid regular expression: {e}")

    def process(self, entry: str) -> List[str]:
        entries = self.m.findall(entry)
        if len(entries) >= 1:
            return entries
        else:
            return None

    def __str__(self):
        return f"{M.op_name()} \"{escape(self.regexp)}\""


