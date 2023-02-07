from typing import List

from dj_ast import Transformer


class AsPrependHcRule(Transformer):
    """ Converts the entry to an Hashcat prepend rule.
        Takes care of the necessary reversing of the term!
        E.g. converts "Test" to "^t^s^e^T".
    """

    def op_name() -> str: return "as_append_hc_rule"

    def process(self, entry: str) -> List[str]:
        if len(entry) > 0:
            return ["^"+"^".join(entry[::-1])]
        else: 
            return [entry]


AS_PREPEND_HC_RULE = AsPrependHcRule()
