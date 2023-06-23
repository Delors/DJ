from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryTransformer
from common import InitializationFailed


class GListDrop(PerEntryTransformer):
    """
    Discards the ending of an entry if it matches any of the strings
    found in the specified global list.
    """

    def op_name() -> str: return "glist_drop"

    MIN_LENGTH = 4 # of characters of the remaining entry

    def __init__(self, listname):
        self.listname = listname
        self.entries_set = None

    def __str__(self):
        return f'{GListDrop.op_name()} {self.listname}'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.listname not in td_unit.global_entry_lists:
            raise InitializationFailed(f"{self}: list does not exist")
        self.entries_set = set(self.td_unit.global_entry_lists[self.listname])
        return self

    def process(self, entry: str) -> list[str]:        
        all = []
        l_entry = len(entry)
        for s in range(l_entry-1,GListDrop.MIN_LENGTH-1,-1):
            part = entry[s:l_entry]
            if part in self.entries_set:
                all.append(entry[0:s])
        if len(all) == 0:
            return None
        else:
            return all


