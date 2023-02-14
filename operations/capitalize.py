from typing import List

from dj_ast import Transformer


class Capitalize(Transformer):
    """Capitalizes a given entry. 
    
        I.e., the first character of a string is converted to a capital letter.
    """

    def op_name() -> str: return "capitalize"

    def process(self, entry: str) -> List[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return None


CAPITALIZE = Capitalize()
