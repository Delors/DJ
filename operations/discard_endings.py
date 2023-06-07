from dj_ast import ASTNode, TDUnit
from dj_ops import PerEntryTransformer
from common import read_utf8file, escape


class DiscardEndings(PerEntryTransformer):
    """
    Discards the last term - recursively - of a string with multiple 
    elements if the term is defined in the given file. The preceding 
    whitespace will also be discarded.

    For example, given the string:

        _Michael ist ein_

    and assuming that "ist" and "ein" should not be endings, the only
    string that will pass this operation would be "Michael".

    (See also the ignore directive for a similar mechanism.)
    """

    def op_name() -> str: return "discard_endings"

    def __init__(self, endings_filename):
        self.endings_filename = endings_filename
        self.endings: set[str] = set()

    def __str__(self):
        return f'{DiscardEndings.op_name()} "{escape(self.endings_filename)}"'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        self.endings = set(read_utf8file(self.endings_filename))
        return self

    def process(self, entry: str) -> list[str]:
        all_terms = entry.split()
        count = 0
        while len(all_terms) > (-count) and \
                all_terms[count - 1] in self.endings:
            count -= 1

        if count != 0:
            return [" ".join(all_terms[0:count])]
        else:
            return None
