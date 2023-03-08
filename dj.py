#!/usr/bin/python3

# Dr. Michael Eichberg (mail@michael-eichberg.de)
# (c) 2022,2023

from sys import stdin, stderr, exit
import argparse
from itertools import chain

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable
from time import time

from parsimonious.exceptions import IncompleteParseError

from common import get_filename, locate_resource, enrich_filename
from common import escape, unescape
from common import read_utf8file
from common import InitializationFailed
from grammar import DJ_GRAMMAR, DJTreeVisitor
from dj_ast import Operation, TDUnit
from dj_ops import ComplexOperation


def transform_entries(td_unit: TDUnit, dictionary_filename: str, report_pace: bool):
    """ Transforms the entries of a dictionary.
        A dictionary can come from three sources; however, at most two sources
        are used.
        1) a generator
        2) a file or stdin
    """
    generators = td_unit.instantiate_generators()

    d_in = None
    if dictionary_filename:
        d_in = open(dictionary_filename, 'r')
    else:
        d_in = stdin

    count = 0
    start = time()
    last_count = 0
    for entry in chain(generators, d_in):
        count = count + 1
        sentry = entry.rstrip("\r\n")
        td_unit.process(count, sentry)
        if report_pace and time()-start > 5:
            print(
                f"[info] processed: {count}; speed: {(count-last_count)//(time()-start)} entries per second", file=stderr)
            last_count = count
            start = time()

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
        help="prints detailed progress information",
        action="store_true"
    )
    parser.add_argument(
        '--pace',
        help="prints speed information",
        action="store_true"
    )
    parser.add_argument(
        '-u',
        '--unique',
        help="an entry is reported only once to the first effective output target; this keeps all entries in memory; do not use on memory-constraint systems with huge dictionaries",
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
    unique = args.unique

    # 1. parse spec to get TDUnit
    raw_td_file = ""
    if args.operations:
        with open(args.operations, mode="r") as f:
            raw_td_file += f.read()
    if args.adhoc_operations and len(args.adhoc_operations) > 0:
        if not raw_td_file.endswith("\n") and len(raw_td_file) > 0:
            raw_td_file += "\n"
        raw_td_file += " ".join(args.adhoc_operations)
    if len(raw_td_file) == 0:
        print("[error] arguments missing; use dj.py -h for help", file=stderr)
        return -1
    try:
        dj_source_tree = DJ_GRAMMAR.parse(raw_td_file)
    except IncompleteParseError as e:
        print("[error] "+str(e), file=stderr)
        return -2

    td_unit: TDUnit = DJTreeVisitor().visit(dj_source_tree)
    td_unit.report_progress = args.progress
    td_unit.verbose = verbose
    td_unit.trace_ops = trace_ops
    td_unit.unique = unique
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
    try:
        td_unit.init(td_unit, None)
    except InitializationFailed as ex:
        print(f"[error] {ex.args[0]}")
        return 1

    # 2. apply operations
    if verbose:
        print(
            "[debug] ============== T R A N S F O R M A T I O N =============", file=stderr)
    transform_entries(td_unit, args.dictionary, args.pace)

    # 3. cleanup operations (in particular closing of file output streams)
    if verbose:
        print(
            "[debug] =================== C L E A N   U P ====================", file=stderr)
    td_unit.close()

    return 0


if __name__ == '__main__':
    exit(main())
