from typing import List

from dj_ast import Transformer


class Title(Transformer):
    """ Converts an entry to title case.

        E.g. "this is a test" is converted to "This Is A Test"

        (In case of a single word, capitalize and title have the 
        same effect.)
    """

    def op_name() -> str: return "title"

    def process(self, entry: str) -> List[str]:
        title = entry.title()
        if title != entry:
            return [title]
        else:
            return None


TITLE = Title()
