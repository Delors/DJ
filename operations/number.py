from dj_ops import PerEntryTransformer


class Number(PerEntryTransformer):
    """ Replaces every matched character by the number 
        of previous occurrences of matched characters.

        E.g. if the _chars to number_ set consists of [aeiou] and
        the string "Bullen jagen" is given, then the result of the
        transformation is: "B1ll2n j3g4n".
    """

    def op_name() -> str: return "number"

    def __init__(self, chars_to_number: str):
        self.chars_to_number = set(chars_to_number)
        
    def __str__(self):
        chars = "".join(self.chars_to_number)
        return f"{Number.op_name()} [{chars}]"    

    def process(self, entry: str) -> list[str]:
        count = 0
        new_e = ""
        for e in entry:
            if e in self.chars_to_number:
                count += 1
                new_e += str(count)
            else:
                new_e += e

        if count == 0:
            return None
        else:
            return [new_e]

