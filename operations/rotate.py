from typing import List

from dj_ast import Transformer


class Rotate(Transformer):
    """ Rotates the entry n chars to the left; e.g., `rotate 1`
        transforms "abc" to "bca".

        (If you want to get the reverse, i.e., "cba" use
        the reverse operation.)
    """
    def __init__(self,rotate_by: int) -> None:
        self.rotate_by = rotate_by

    def op_name() -> str: return "rotate"

    def process(self, entry: str) -> List[str]:
        
        rotated_entry = entry[self.rotate_by:] + entry[0:self.rotate_by]

        if rotated_entry != entry:
            return [rotated_entry]
        else:
            return None

    def __str__(self):
        return f"{Rotate.op_name()} {self.rotate_by}"

