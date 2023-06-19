
from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryTransformer
from common import InitializationFailed, escape


class Map(PerEntryTransformer):
    """ Maps each given character to one to several alternatives.

        Example
            map "abc" "l"
        Input
            12abc&
        Output
            12lll&

        Example
            map "ab" "xy"
        Input
            12abc&
        Output
            12xx&
            12yx&
            12yy&
            12xy&

    """

    def op_name() -> str: return "map"

    def __init__(self, map_not : bool, source_chars: str, target_chars: str):
        self.map_not = map_not
        self.raw_source_chars = source_chars
        self.source_chars = set(source_chars)
        self.raw_target_chars = target_chars
        self.target_chars = set(target_chars)

    def __str__(self):
        map_not = Map.op_name()
        if self.map_not:
            map_not += " not"
        source_chars = escape(self.raw_source_chars)
        target_chars = escape(self.raw_target_chars)
        return f'{map_not} "{source_chars}" "{target_chars}"'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if len(self.source_chars) == 0:
            raise InitializationFailed(
                f"{self}: invalid length for source chars")
        if len(self.target_chars) == 0:
            raise InitializationFailed(
                f"{self}: invalid length for target chars")
        if not self.source_chars.isdisjoint(self.target_chars):
            msg = f'{self}: useless identity mapping {self.source_chars.intersection(self.target_chars)}"'
            raise InitializationFailed(msg)
        return self

    def process(self, entry: str) -> list[str]:
        hit = False
        new_entries = [""]
        for e in entry:
            in_source_chars = e in self.source_chars
            if (in_source_chars and not self.map_not) or (not in_source_chars and self.map_not) :
                hit = True
                es = []
                for t in self.raw_target_chars:
                    for new_e in new_entries:
                        es.append(new_e + t)
                new_entries = es
            else:
                new_entries = list(map(lambda new_e: new_e+e, new_entries))

        if hit:
            return new_entries
        else:
            return None
