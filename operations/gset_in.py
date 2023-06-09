from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryFilter
from common import InitializationFailed


class GListIn(PerEntryFilter):
    """
    Filters (i.e. passes on) those elements that are defined 
    in the global set.
    """

    def op_name() -> str: return "glist_in"

    def __init__(self, setname):
        self.setname = setname
        self.entries_set = None

    def __str__(self):
        return f'{GListIn.op_name()} {self.setname}'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.setname not in td_unit.global_entry_sets:
            msg = f"{self}: global set does not exist"
            raise InitializationFailed(msg)
        self.entries_set = self.td_unit.global_entry_sets[self.setname]        
        return self

    def process(self, entry: str) -> list[str]: 
        if entry in self.entries_set:
            return [entry]
        else:
            return []


