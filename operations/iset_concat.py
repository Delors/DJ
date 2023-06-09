from dj_ast import Transformer
from common import escape


class IListConcat(Transformer):
    """ Concats all current intermediate results. 
        None is returned if the current set only consists of one 
        intermediate result.
    """

    def op_name() -> str: return "ilist_concat"

    def __init__(self, s: str):
        """
        s Str used to concat the entries.
        """
        self.s = s

    def __str__(self):
        if len(self.s) > 0 :
            return f'{IListConcat.op_name()} "{escape(self.s)}"'
        else:
            return f'{IListConcat.op_name()}'

    def process_entries(self, entries: list[str]) -> list[str]:
        if len(entries) == 1:
            return None

        new_e = self.s.join(entries)
        if not new_e in self.td_unit.ignored_entries:
            return [new_e]
        elif self.td_unit.trace_ops:
            print(f"[trace] ignored derived entry: {new_e}")


