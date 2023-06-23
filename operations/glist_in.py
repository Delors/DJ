from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryFilter
from common import InitializationFailed


class GListIn(PerEntryFilter):
    """
    Filters (i.e. passes on) those elements that are defined 
    in the global set.
    """

    def op_name() -> str: return "glist_in"

    def __init__(self, listname):
        self.listname = listname
        self.entries_set = None

    def __str__(self):
        return f'{GListIn.op_name()} {self.listname}'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.listname not in td_unit.global_entry_lists:
            msg = f"{self}: global list does not exist"
            raise InitializationFailed(msg)
        self.entries_set = set(self.td_unit.global_entry_lists[self.listname])
        return self

    def process(self, entry: str) -> list[str]:
        if entry in self.entries_set:
            return [entry]
        else:
            return []
