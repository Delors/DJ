from dj_ops import PerEntryTransformer


class FoldWS(PerEntryTransformer):
    """Folds multiple whitespace (spaces and tabs) to one space."""

    def op_name() -> str: return "fold_ws"

    def process(self, entry: str) -> list[str]:
        last_entry = ""
        folded_entry = entry
        while folded_entry != last_entry:
            last_entry = folded_entry
            folded_entry = folded_entry\
                .replace("  ", " ")\
                .replace("\t", " ")  # May result in 2 or 3 subsequent spaces
        if entry != folded_entry:
            return [folded_entry]
        else:
            return None


FOLD_WS = FoldWS()
