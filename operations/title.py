from dj_ops import PerEntryTransformer


class Title(PerEntryTransformer):
    """ Converts an entry to title case.

        E.g. "this is a test" is converted to "This Is A Test"

        (In case of a single word, capitalize and title have the 
        same effect.)
    """

    def op_name() -> str: return "title"

    def process(self, entry: str) -> list[str]:
        title = entry.title()
        if title != entry:
            return [title]
        else:
            return None


TITLE = Title()
