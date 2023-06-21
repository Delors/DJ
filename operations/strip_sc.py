from dj_ops import PerEntryTransformer


class StripSC(PerEntryTransformer):
    """Removes non alpha-numeric letters at the beginning or end."""

    def op_name() -> str: return "strip_sc"

    def process(self, entry: str) -> list[str]:
        stripped_entry = entry

        left = 0
        for e in entry:
            if not e.isalnum():
                left += 1
            else:
                break
        right = len(entry)    
        for i in range(len(entry)-1,0,-1):
            if not entry[i].isalnum():
                right = i
            else:
                break

        if right == 0:
            return []
        if left == 0 and right == len(entry):
            # there were no special characters
            return None

        return [entry[left:right]]

STRIP_SC = StripSC()