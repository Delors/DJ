from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryTransformer
from common import InitializationFailed, read_utf8file, escape


class Replace(PerEntryTransformer):
    """ Replaces a character (sequence) by another character (sequence).

        (If you want to replace a single character by multiple other 
        characters use the "map" operation.)
    """

    def op_name() -> str: return "replace"

    def __init__(self, replacements_filename):
        self.replacements_filename = replacements_filename
        self.replacement_table: dict[str, str] = {}

    def __str__(self):
        return f'{Replace.op_name()} "{escape(self.replacements_filename)}"'

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
                raise InitializationFailed(
                    f"{self} contains invalid entry: {sline}")
            key = "\\".join(
                list(map(lambda s: s.replace("\\s", " ")
                         .replace("\\#", "#"),
                     raw_key.split("\\\\"))
                     ))
            value = "\\".join(
                list(map(lambda s: s.replace("\\s", " ")
                         .replace("\\#", "#"),
                     raw_value.split("\\\\"))
                     ))

            if self.replacement_table.get(key):
                msg = f"{self}: {key} is already used"
                raise InitializationFailed(msg)

            if self.replacement_table.get(value):
                msg = f"{self}: the value {value} is later used as a key"
                raise InitializationFailed(msg)

            self.replacement_table[key] = value
        return self

    def process(self, entry: str) -> list[str]:
        e = entry
        for k, v in self.replacement_table.items():
            # RECALL:   Replace maintains object identity if there is
            #           nothing to replace.
            e = e.replace(k, v)
        if entry is e:
            return None
        else:
            return [e]
