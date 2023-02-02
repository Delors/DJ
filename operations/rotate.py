from typing import List

from dj_ast import Transformer


class Rotate(Transformer):
    """Rotates the entry; e.g., "abc" is transformed to "cba"."""

    def op_name() -> str: return "rotate"

    def process(self, entry: str) -> List[str]:
        r = []
        for i in entry:
            r = [i] + r
        rotated_entry = "".join(r)

        if rotated_entry != entry:
            return [rotated_entry]
        else:
            return None


ROTATE = Rotate()
