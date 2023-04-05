from typing import List

from dj_ast import TDUnit, ASTNode, Transformer
from common import InitializationFailed, read_utf8file, escape


class Replace(Transformer):
    """ Replaces a character by another character.

        (If you want to replace a single character by multiple other 
        characters use the "map" operation.)
    """

    def op_name() -> str: return "replace"

    def __init__(self, replacements_filename):
        self.replacements_filename = replacements_filename
        self.replacement_table: dict[str, str] = {}

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        entries = read_utf8file(self.replacements_filename)
        for line in entries:
            sline = line.strip()
            if sline.startswith("#"):
                continue
            try:
                (raw_key, raw_value) = sline.split()
            except:
                raise InitializationFailed(f"{self} contains invalid entry: {sline}")
            key = raw_key\
                .replace("\\s", " ")\
                .replace("\#", "#")\
                .replace("\\\\", "\\")
            value = raw_value\
                .replace("\\s", " ")\
                .replace("\#", "#")\
                .replace("\\\\", "\\")
            current_values = self.replacement_table.get(key)
            if current_values:
                msg = f"{self}: {key} is already used"
                raise InitializationFailed(msg)
            else:
                self.replacement_table[key] = value

    def process(self, entry: str) -> List[str]:
        e = entry
        for k, v in self.replacement_table.items():
            # RECALL:   Replace maintains object identity if there is
            #           nothing to replace.
            e = e.replace(k, v)
        if entry is e:
            return None
        else:
            return [e]

    def __str__(self):
        return f'{Replace.op_name()} "{escape(self.replacements_filename)}"'
