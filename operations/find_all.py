import re
from typing import List

from dj_ast import Extractor, TDUnit, ASTNode
from common import escape, InitializationFailed


class FindAll(Extractor):
    """ Uses the given regular expressions to find all corresponding words.
        E.g. to extract subwords, the regular expression 
        "'[A-Z][a-z]*'" could be used.

        # Example Usage
        `./dj.py 'find_all "[A-Z][a-z]*" report'`
    """

    def op_name() -> str: return "find_all"

    def __init__(self, regexp : str) -> None:
        super().__init__()
        self.regexp = regexp
        self.m = None # the matcher that will be derived from the regexp at "init" time

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        try:
            self.m = re.compile(self.regexp)
        except Exception as e:
            raise InitializationFailed(
                f"{self}: {e} is an invalid regular expression")

    def process(self, entry: str) -> List[str]:
        entries = self.m.findall(entry)
        if len(entries) >= 1:
            if isinstance(entries[0],str):
                return entries
            # obviously capturing groups were used...
            all = []
            for entry in entries:
                all.extend(entry)
            return all
        else:
            return None

    def __str__(self):
        return f"{FindAll.op_name()} \"{escape(self.regexp)}\""


