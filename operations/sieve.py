from typing import List

from common import locate_resource
from operations.operation import Filter

class Sieve(Filter):
    """Only accepts entries which consists of the chars found in the specified file."""

    def __init__(self, sieve_filename : str):
        self.sieve_filename = sieve_filename
        abs_filename = locate_resource(sieve_filename)
        chars = set()
        with open(abs_filename,"r", encoding='utf-8') as sieve_file :
            for line in sieve_file:
                for c in line:
                    if c != '\r' and c != '\n':
                        chars.add(c)                
        self._chars = chars
        return

    def process(self, entry: str) -> List[str]:
        if all(c in self._chars for c in entry):
           return [entry]
        else:
            return []

    def __str__(self):
        return f"sieve \"{self.sieve_filename}\""

