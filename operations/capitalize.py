from dj_ops import PerEntryTransformer


class Capitalize(PerEntryTransformer):
    """Capitalizes a given entry. 
    
        I.e., the first character of a string is converted to a capital letter.
    """

    def op_name() -> str: return "capitalize"

    def process(self, entry: str) -> list[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return None


CAPITALIZE = Capitalize()
