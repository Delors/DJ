from typing import List, Set

from operations.operation import Transformer
from common import locate_resource

class DiscardEndings(Transformer):
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

    def __init__(self, endings_filename):
        self.endings_filename = endings_filename

        endings : Set[str] = set()
        endings_resource = locate_resource(endings_filename)
        with open(endings_resource,"r",encoding="utf-8") as fin :
            for ending in fin:
                endings.add(ending.rstrip("\r\n"))       
        self.endings = endings

    def process(self, entry: str) -> List[str]: 
        all_terms = entry.split()
        count = 0
        while len(all_terms) > (-count) and \
              all_terms[count -1] in self.endings:
            count -= 1

        if count != 0:
            return [" ".join(all_terms[0:count])]
        else:
            return None
        
    def __str__(self):
        return f'discard_endings "{self.endings_filename}"'