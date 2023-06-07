from dj_ast import TDUnit, ASTNode
from dj_ops import PerEntryTransformer
from common import InitializationFailed, read_utf8file, escape


class MultiReplace(PerEntryTransformer):
    """ Replaces a character (seq) by other character sequences.

        Given the following replacement table:
            xx 1
            xx 2
            yy 5
            y 4
            y 8

        and the following entry
            xxabcyy

        and the setting that we will apply max two different 
        replacements per word, then the result will be:
        # just one replacement
            1abcyy
            2abcyy
            xxabc5
            xxabc44
            xxabc88
        # two replacements
            1abc5
            2abc5
            1abc44
            2abc44
            1abc88
            2abc88

        In the replacement file:
         - a space seperates the key and the value
         - # at the beginning of a line signifies a comment
         - \ is the escape symbol
         - \s is the escape sequence for a space

        So - be careful ... the number of generated entries can be really huge.

         -  If you want to replace all occurrences of a character sequence
            by a specific character sequence use the replace operation.
            (`replace` handles the base case; `multi_replace` handles more
            complicated use cases.)
         -  If you want to replace a single character by multiple other 
            characters use the "map" operation.
    """

    APPLY_UP_TO_N_REPLACEMENTS = 2

    def op_name() -> str: return "multi_replace"

    def __init__(self, replacements_filename):
        self.replacements_filename = replacements_filename
        self.replacement_table: dict[str, list[str]] = {}

    def __str__(self):
        return f'{MultiReplace.op_name()} "{escape(self.replacements_filename)}"'

    def init(self, td_unit: TDUnit, parent: ASTNode):
        super().init(td_unit, parent)
        if self.APPLY_UP_TO_N_REPLACEMENTS < 1:
            raise InitializationFailed(
                f"{self} APPLY_UP_TO_N_REPLACEMENTS < 1")

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
            if key == value:
                raise InitializationFailed(f"{self} key == value: {sline}")
            current_values = self.replacement_table.get(key)
            if current_values:
                current_values.append(value)
            else:
                self.replacement_table[key] = [value]
        return self

    def process(self, entry: str) -> list[str]:
        # Initialize the table
        all = []
        all_dict: dict[int, list[str]] = {}
        for i in range(1, self.APPLY_UP_TO_N_REPLACEMENTS+1):
            all_dict[i] = []

        for k, vs in self.replacement_table.items():
            for v in vs:
                for r in range(self.APPLY_UP_TO_N_REPLACEMENTS-1, 0, -1):
                    for e in all_dict[r]:
                        new_entry = e.replace(k, v)
                        if new_entry != e:
                            all.append(new_entry)
                            all_dict[r+1].append(new_entry)

                new_entry = entry.replace(k, v)
                if new_entry != entry:
                    all.append(new_entry)
                    all_dict[1].append(new_entry)

        if len(all) == 0:
            return None
        else:
            return all
