# -*- coding: utf-8 -*-
from typing import List

from dj_ast import ASTNode, TDUnit, Filter
from common import InitializationFailed, escape


class IsPartOf(Filter):
    """ Tests if a given entry is part of the specified sequence.

        For example "cde" is part of the sequence "abcdefghijklmnopqrstuvwxyz".
    """

    ENTRY_MIN_LENGTH = 4
    """ Only entries of the given minimum length are checked for being
        a part of the specified sequence.
    """

    def op_name() -> str: return "is_part_of"

    def __init__(self, sequence: str) -> None:
        self.sequence = sequence

    def init(self, td_unit: TDUnit, parent: ASTNode, verbose: bool):
        super().init(td_unit, parent, verbose)
        if len(self.sequence) < 2:
            raise InitializationFailed(
                f"{self}: a sequence has to have at least two characters")
        if len(self.sequence) < IsPartOf.ENTRY_MIN_LENGTH:
            raise InitializationFailed(
                f"{self}: the length of the sequence is smaller than ENTRY_MIN_LENGTH"
            )

    def is_filter(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if len(entry) < IsPartOf.ENTRY_MIN_LENGTH:
            # TODO Do we want to introduce the concept of a filter that does not apply?
            return []

        if entry in self.sequence:
            return [entry]
        else:
            return []

    def __str__(self):
        return f'{IsPartOf.op_name()} "{escape(self.sequence)}"'
