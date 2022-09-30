from typing import List

from operations.operation import Operation


class StripNumbersAndSpecialChars(Operation):
    """Removes leading and trailing numbers and special chars."""

    def is_transformer(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        strip_chars = "0123456789<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-"
        stripped_entry = entry.strip(strip_chars)
        if stripped_entry is entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of stripped entries
            return []
        else: # stripped_entry != entry:
            # The entry is not empty
            return [stripped_entry]

    def __str__(self):
        return "strip_numbers_and_sc"

STRIP_NUMBERS_AND_SPECIAL_CHARS = StripNumbersAndSpecialChars()    