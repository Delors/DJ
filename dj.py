#!/usr/bin/python3

# Dr. Michael Eichberg (mail@michael-eichberg.de)
# (c) 2022

from sys import stdin, stderr, exit
import argparse
import traceback

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from parsimonious.exceptions import IncompleteParseError

from common import get_filename, locate_resource, enrich_filename
from common import escape, unescape
from common import read_utf8file
from grammar import DJ_GRAMMAR, DJTreeVisitor
from dj_ast import Operation, TDUnit
from dj_ops import ComplexOperation


# ignored_entries = set()
# """ The global list of all entries which will always be ignored.
#     Compared to an operation which only processes an entry at
#     a specific point in time, an entry will - after each step -
#     always be checked against entries in the ignored_entries set.
# """

# sets : Tuple[str,List[str]] = {}
# """ The sets which are created while processing the entries. The
#    sets are cleared whenever a new dictionary entry is analyzed.
# """

# def _clear_sets():
#    for k in sets.keys(): sets[k] = []


# def apply_ops(entry : str, ops : List[Operation]) -> List[str]:
#    """ Applies all operations to the given entry. As a result multiple new
#        entries may be generated. None is returned if and only if the
#        application of an operation to all (intermediate) entries resulted in
#        `None`. (cf. Operation.processEntries)
#    """
#        self.td_unit.
#        try:
#            new_entries = op.process_entries(entries)
#        except Exception as e:
#            print(traceback.format_exc())
#            print(f"[error] {op}({entries}) failed: {str(e)}",file=stderr)
#            return
#
#        if _trace_ops:
#            print(f"[trace] result:   {new_entries}",file=stderr)
#
#        if new_entries is None:
#            return None
#
#        entries = []
#        for new_entry in new_entries:
#            if len(new_entry) == 0:
#                continue
#            if new_entry in ignored_entries:
#                if _trace_ops:
#                    print(f"[trace] ignoring: {new_entry}")
#            else:
#                entries.append(new_entry)
#
#        if len(entries) == 0:
#            return []
#
#    return entries


def transform_entries(td_unit: TDUnit, dictionary_filename: str):
    """Transforms the entries of a given dictionary."""
    d_in = None
    if dictionary_filename:
        d_in = open(dictionary_filename, 'r')
    else:
        d_in = stdin

    count = 0
    for entry in d_in:
        count = count + 1
        sentry = entry.rstrip("\r\n")
        td_unit.process(count, sentry)

    if dictionary_filename:  # test that we don't close stdin
        d_in.close()


def main() -> int:

    parser = argparse.ArgumentParser(
        description="""Generates an attack dictionary based on a plain dictionary."""
    )
    parser.add_argument(
        '-o',
        '--operations',
        help="a .td file with the operations/transformation directives that will be applied to the dictionary entries"
    )
    parser.add_argument(
        '-d',
        '--dictionary',
        help="the input dictionary (if not specified stdin is used)"
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help="prints general trace information",
        action="store_true"
    )
    parser.add_argument(
        '-t',
        '--trace_ops',
        help="prints extensive trace information about ops",
        action="store_true"
    )
    parser.add_argument(
        '-p',
        '--progress',
        help="prints progress information",
        action="store_true"
    )
    parser.add_argument(
        'adhoc_operations',
        metavar='OPs',
        type=str,
        nargs='*',
        help='an operations definition')

    args = parser.parse_args()
    verbose = args.verbose
    trace_ops = args.trace_ops

    # 1. parse spec to get TDUnit
    raw_td_file = ""
    if args.operations:
        with open(args.operations, mode="r") as f:
            raw_td_file += f.read()
    if args.adhoc_operations and len(args.adhoc_operations) > 0:
        raw_td_file += "\n" + " ".join(args.adhoc_operations)
    try:
        dj_source_tree = DJ_GRAMMAR.parse(raw_td_file)
    except IncompleteParseError as e:
        print(str(e), file=stderr)
        return -1

    td_unit: TDUnit = DJTreeVisitor().visit(dj_source_tree)
    td_unit.report_progress = args.progress
    td_unit.verbose = verbose
    td_unit.trace_ops = trace_ops
    if verbose:
        ast = "\n".join(
            map(lambda l: "[debug] " + l, str(td_unit).splitlines()))
        print(
            "[debug] ================== P A R S E D   A S T =================", file=stderr)
        print(ast, file=stderr)

    # 2. initialization & validation
    if verbose:
        print(
            "[debug] ============== I N I T I A L I Z A T I O N =============", file=stderr)
    td_unit.init(td_unit, None, verbose=verbose)

    # 2. apply operations
    if verbose:
        print(
            "[debug] ============== T R A N S F O R M A T I O N =============", file=stderr)
    transform_entries(td_unit, args.dictionary)

    # 3. cleanup operations (in particular closing of file output streams)
    if verbose:
        print(
            "[debug] ==================== C L E A N   U P ===================", file=stderr)
    td_unit.close()

    return 0


if __name__ == '__main__':
    exit(main())
