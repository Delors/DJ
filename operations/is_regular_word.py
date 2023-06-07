from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryFilter
from common import dictionaries as all_dictionaries


class IsRegularWord(PerEntryFilter):
    """ Checks if a word is a _real_ word by looking it up in several
        dictionaries; for that the lower case variant of the entry and
        the capitalized variant is tested. 

        The set of dictionaries that is used is based 
        on those defined in `common.dictionaries`.
    """

    def op_name() -> str: return "is_regular_word"

    DICTIONARIES = ["de","en"]

    def __init__(self) -> None:
        self.dictionaries = []

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        for d in IsRegularWord.DICTIONARIES:
            self.dictionaries.append((d,all_dictionaries[d]))
        return self

    def do_process(self, entry: str) ->  tuple[str,str]:
        lentry = entry.lower()
        centry = entry.capitalize()
        for (lang,dict) in self.dictionaries:
            try:
                if dict.spell(lentry):
                    return (lentry,lang)
                if dict.spell(centry):
                    return (centry,lang)
            except:
                pass

        return None

    def process(self, entry: str) -> list[str]:
        r = self.do_process(entry)
        if r is not None:
            return [entry]
        else:
            return []


    def derive_rules(self, entry: str) -> list[tuple[str,str]]:
        # Returned value: the first string is the result of the 
        #                 operation; the second is the operation
        #                 to regenerate the original string.
        r = self.do_process(entry)
        print(r)
        if r is not None:
            (accepted_word,lang) = r
            generator_rule = ""
            if accepted_word != entry:
                case_changes = []
                for i in range(0,len(accepted_word)):
                    if accepted_word[i] != entry[i]:
                        case_changes.append(i)
                if len(case_changes) == 1 and case_changes[0] == 0:
                    if accepted_word[0].isupper():
                        generator_rule += "lower\n"
                    else:
                        generator_rule += "capitalize\n"
                elif len(case_changes) >= 1:
                    for i in case_changes:
                        if accepted_word[i].isupper():
                            generator_rule += f"lower {i}\n"
                        else:
                            generator_rule += f"upper {i}\n"

            generator_rule += f"regular_word {len(entry)} {lang}\n"
            return [(entry,generator_rule)]
                
        return r
