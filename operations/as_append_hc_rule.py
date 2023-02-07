from typing import List

from dj_ast import Transformer


class AsAppendHcRule(Transformer):
    """ Converts the entry to an Hashcat append rule.
        E.g. converts "Test" to "$T$e$s$t".
    """

    def op_name() -> str: return "as_append_hc_rule"

    def process(self, entry: str) -> List[str]:
        if len(entry) > 0:
            return ["$"+"$".join(entry)]
        else: 
            return [entry]


AS_APPEND_HC_RULE = AsAppendHcRule()
