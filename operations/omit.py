from dj_ops import PerEntryExtractor


class Omit(PerEntryExtractor):
    """ Removes the character at the specified location (zero based).

        A typical use case is:
        
        `+omit 8 +omit 7 +omit 6 +omit 5 +omit 4 +omit 3 +omit 2 +omit 1 +omit 0`

        (Note the reverse order to ensure that __all__ variants are created!)
    """

    def op_name() -> str: return "omit"

    def __init__(self, pos: int):
        self.pos = pos

    def __str__(self):
        return f"{Omit.op_name()} {self.pos}"

    def process(self, entry: str) -> list[str]:
        pos = self.pos
        if pos >= len(entry):
            return None
        new_entry = entry[0:pos] + entry[pos+1:len(entry)+1]
        if len(new_entry) == 0:
            return []
        else:
            return [new_entry]

