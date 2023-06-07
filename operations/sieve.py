from common import read_utf8file, escape
from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryFilter


class Sieve(PerEntryFilter):
    """ Only accepts entries which consist of the chars found in the 
        specified file.
    """

    def op_name() -> str: return "sieve"

    def __init__(self, sieve_filename: str):
        self.sieve_filename = sieve_filename
        self.chars = set()

    def __str__(self):
        return f"{Sieve.op_name()} \"{escape(self.sieve_filename)}\""

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        for line in read_utf8file(self.sieve_filename):
            # recall that the lines are already rigth-stripped.
            for c in line:
                self.chars.add(c)
        return self

    def process(self, entry: str) -> list[str]:
        if all(c in self.chars for c in entry):
            return [entry]
        else:
            return []
