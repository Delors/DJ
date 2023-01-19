from typing import List

from common import read_utf8file, escape
from dj_ast import TDUnit, ASTNode, Filter

class Sieve(Filter):
    """Only accepts entries which consists of the chars found in the specified file."""

    def op_name() -> str: return "sieve"

    def __init__(self, sieve_filename : str):        
        self.sieve_filename = sieve_filename
        self.chars = set()


    def init(self, td_unit: TDUnit, parent: ASTNode, verbose : bool):    
        super().init(td_unit,parent,verbose)
        for line in read_utf8file(self.sieve_filename):
            # recall that the lines are already rigth-stripped.
            for c in line:
                self.chars.add(c)                


    def process(self, entry: str) -> List[str]:
        if all(c in self.chars for c in entry):
            return [entry]
        else:
            return []


    def __str__(self):
        return f"{Sieve.op_name()} \"{escape(self.sieve_filename)}\""

