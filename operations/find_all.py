import re

from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryExtractor
from common import escape, InitializationFailed


class FindAll(PerEntryExtractor):
    """ Uses the given regular expressions to find all corresponding words.
        E.g. to extract subwords, the regular expression 
        "'[A-Z][a-z]*'" could be used.

        # Example Usage
        `./dj.py 'find_all "[A-Z][a-z]*" report'`
    """

    def op_name() -> str: return "find_all"

    def __init__(self, join : bool, regexp : str) -> None:
        super().__init__()
        self.regexp = regexp
        self.join = join
        self.m = None # the matcher that will be derived from the regexp at "init" time

    def __str__(self):
        join_str = ' join ' if self.join else ' '
        return f"{FindAll.op_name()}{join_str}\"{escape(self.regexp)}\""

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        try:
            self.m = re.compile(self.regexp)
        except Exception as e:
            raise InitializationFailed(
                f"{self}: {e} is an invalid regular expression")
        return self

    def process(self, entry: str) -> list[str]:
        entries = self.m.findall(entry)
        if len(entries) >= 1:
            if isinstance(entries[0],str):
                return entries
            # obviously capturing groups were used...            
            if self.join:            
                return ["".join(map(lambda t: "".join(t) ,entries))]
            else:
                all = []
                for entry in entries:
                    all.extend(entry)
                return all
        else:
            return None




