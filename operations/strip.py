from dj_ast import TDUnit,ASTNode
from dj_ops import PerEntryTransformer
from common import escape, InitializationFailed


class Strip(PerEntryTransformer):
    """Removes leading and trailing chars as specified."""

    def op_name() -> str: return "strip"

    def __init__(self,chars) -> None:
        self.chars = chars

    def __str__(self):
        return f"{Strip.op_name()} {escape(self.chars)}"

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.chars) == 0:
            raise InitializationFailed(f"{self}: nothing to strip")
        if len(set(self.chars)) != len(self.chars):
            raise InitializationFailed(f"{self}: set contains duplicates")
        return self

    def process(self, entry: str) -> list[str]:
        stripped_entry = entry.strip(self.chars)
        if stripped_entry is entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of stripped entries
            return []
        else:  # stripped_entry != entry:
            # The entry is not empty
            return [stripped_entry]

