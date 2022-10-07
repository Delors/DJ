#!/usr/bin/python3

# Bundeskriminalamt KT53
# Dr. Michael Eichberg (michael.eichberg@bka.bund.de)
# (c) 2022

import sys
from sys import stderr
import os
import argparse
import re

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from common import IllegalStateError,escape,unescape,get_filename,locate_resource
from operations.detriplicate import DETRIPLICATE

from operations.operation import Operation
# TRANSFORMERS
from operations.deleetify import DELEETIFY
from operations.remove_whitespace import REMOVE_WHITESPACE
from operations.capitalize import CAPITALIZE
from operations.lower import LOWER
from operations.upper import UPPER
from operations.fold_whitespace import FOLD_WHITESPACE
from operations.remove_numbers import REMOVE_NUMBERS
from operations.remove_sc import REMOVE_SPECIAL_CHARS
from operations.strip_ws import STRIP_WHITESPACE
from operations.strip_numbers_and_special_chars import STRIP_NUMBERS_AND_SPECIAL_CHARS
from operations.mangle_dates import MANGLE_DATES
from operations.replace import Replace
from operations.map import Map
from operations.split import Split
from operations.sub_splits import SubSplits
from operations.discard_endings import DiscardEndings
from operations.number import Number
from operations.correct_spelling import CORRECT_SPELLING
from operations.related import RELATED
# EXTRACTORS
from operations.get_numbers import GET_NUMBERS
from operations.get_sc import GET_SPECIAL_CHARS
from operations.deduplicate import DEDUPLICATE
# FILTERS
from operations.min_length import MinLength
from operations.max_length import MaxLength
from operations.is_regular_word import IS_REGULAR_WORD
from operations.is_popular_word import IS_POPULAR_WORD
from operations.is_pattern import IS_PATTERN


_reported_entries : Set[str] = set()
""" The set of reported, i.e., printed, entries per entry. This list is cleared
    by the `transform_entries` method after completely processing an entry.
    """

_verbose = False
_trace_ops = False    

def report(s : str):
    """Prints out the entry if it was not yet printed as part of the mangling
       of the same entry.
    """
    if s not in _reported_entries:
        _reported_entries.add(s)
        print(s)


ignored_entries = set()
""" The global list of all entries which will always be ignored.
    Compared to an operation which only processes an entry at
    a specific point in time, an entry will - after each step -
    always be checked against entries in the ignored_entries set.
"""


def apply_ops(entry : str, ops : List[Operation]) -> List[str]:
    """ Applies all operations to the given entry. As a result multiple new 
        entries may be generated. None is returned if and only if the 
        application of an operation to all (intermediate) entries results in 
        `None`.
    """
    
    entries = [entry]    
    for op in ops:
        all_none = True
        new_entries = []
        for entry in entries:
            if len(entry) > 0:
                try:
                    new_candidate_entries = op.process(entry)
                    if _trace_ops:
                        print(f"[trace] {op}({entry}): {new_candidate_entries}",file=stderr)
                    if new_candidate_entries is not None:
                        all_none = False
                        for new_entry in new_candidate_entries:
                            if new_entry not in ignored_entries:
                                new_entries.append(new_entry)
                            elif _trace_ops:
                                print(f"[trace] <ignored>: '{new_entry}'",file=stderr)
                except Exception as e:
                    print(f"operation {op} failed: {e}",file=stderr)
                    raise
        entries = new_entries

        if len(entries) == 0:
            if all_none:
                return None
            else:
                return []

    return entries


class Report(Operation):
    """The "report" operation prints out the entry. 

    A report generally terminates a sequence of operations, but it
    can also be used if an intermediate result is actually a desired 
    output and we do not want to have multiple operations. For example:

    report ___remove\_ws capitalize report___

    In the above case, we first print out the (original) entry. After
    that white space is removed. This will also filter the set of 
    entries down to those which had white space in the first place 
    and then those entries will be capitalized. For example,
    given the two entries:

        TestTest
        Dies ist ein Test

    the output will be:

        TestTest            [output due to initial report]
        Dies ist ein Test   [output due to initial report]
        Diesisteintest      [after removing ws and capitalization]

    notably:
    
        Testtest
        DiesisteinTest
    
    will not be output.
    """

    def is_reporter(self) -> bool: return True   

    def process(self, entry: str) -> List[str]:
        report(entry)
        return [entry]

    def __str__(self):
        return "report"

REPORT = Report()        


class Macro(Operation):
    """Definition of a macro."""

    def __init__(self, name :str, ops : List[Operation]):
        self.name = name
        self.ops = ops
        return

    def is_macro(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        return apply_ops(entry,self.ops)

    def __str__(self):
        return self.name


class KeepAlwaysModifier(Operation):
    """ Modifies the behavior of the wrapped transformer/extractor
        such that all input entries will also be output entries 
        additionally to those that are newly created by the 
        wrapped operation.
    """

    def __init__(self, op : Operation):
        self.op = op

        if not op.is_transformer() and not op.is_extractor():
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = []
        entries.append(entry)
        return entries
        
    def __str__(self):
        return "+" + str(self.op)


class KeepOnlyIfFilteredModifier(Operation):
    """ Modifies the behavior of the wrapped operation such that an
        input entry will be an output entry if the wrapped operation
        does not apply to the entry. I.e., if the wrapped operation 
        returns None, the entry is passed on otherwise the result
        of the wrapped operation is passed on as is.
    """

    def __init__(self, op : Operation):
        self.op = op

        if not (op.is_transformer() or op.is_extractor()):
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = [entry]
        return entries
        
    def __str__(self):
        return "*" + str(self.op)        


class NegateFilterModifier(Operation):
    """ Modifies the behavior of the wrapped filter such that if the 
        given entry is returned by the underlying filter, an empty 
        list will be returned and vice versa.
    """

    def __init__(self, op : Operation):
        self.op = op

        if not (op.is_filter()):
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries == []:
            return [entry]
        else:
            return []
        
    def __str__(self):
        return "!" + str(self.op)        


class ComplexOperation:
    """ Representation of a complex operation.

        Instantiation of a complex operation which is made up of 
        multiple atomic operations. An instance of ComplexOperation 
        basically just handles applying the atomic operations to 
        an entry and (potentially) every subsequently created entry.
    """

    def __init__(self, ops: List[Operation]):
        if not ops or len(ops) == 0:
            raise ValueError(f"no operations specified: {ops}")

        self.ops = ops
        return

    def apply(self, entry):
        return apply_ops(entry,self.ops)

    def __str__(self) -> str:
        return " ".join(map(str,self.ops))


### PARSER SETUP AND CONFIGURATION

re_next_word = re.compile("^[^\s]+")
re_next_quoted_word = re.compile('^"[^"]+"')

def parse(operation) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations without parameters."""

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        return (rest_of_op,operation)

    return parse_it   

def parse_min_length(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    min_length_match = re_next_word.match(rest_of_op)
    min_length = int(min_length_match.group(0))
    new_rest_of_op = rest_of_op[min_length_match.end(0):].lstrip()
    return (new_rest_of_op,MinLength(min_length))

def parse_max_length(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    max_length_match = re_next_word.match(rest_of_op)
    max_length = int(max_length_match.group(0))
    new_rest_of_op = rest_of_op[max_length_match.end(0):].lstrip()
    return (new_rest_of_op,MaxLength(max_length))

def parse_number(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    chars_to_number_match = re_next_word.match(rest_of_op)
    raw_chars_to_number = chars_to_number_match.group(0)
    chars_to_number = unescape(raw_chars_to_number)
    new_rest_of_op = rest_of_op[chars_to_number_match.end(0):].lstrip()
    return (new_rest_of_op,Number(chars_to_number[1:-1] ))# get rid of the set braces "[" and "]".

def parse_map(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    source_char_match = re_next_word.match(rest_of_op)
    raw_source_char = source_char_match.group(0)
    source_char = unescape(raw_source_char)
    rest_of_op = rest_of_op[source_char_match.end(0):].lstrip()

    target_chars_match = re_next_word.match(rest_of_op)
    raw_target_chars = target_chars_match.group(0)
    target_chars = unescape(raw_target_chars)
    new_rest_of_op = rest_of_op[target_chars_match.end(0):].lstrip()

    return (new_rest_of_op,Map(source_char,target_chars[1:-1]))    

def parse_split(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    split_chars_match = re_next_word.match(rest_of_op)
    raw_split_chars = split_chars_match.group(0)
    split_char = unescape(raw_split_chars)
    new_rest_of_op = rest_of_op[split_chars_match.end(0):].lstrip()
    return (new_rest_of_op,Split(split_char))

def parse_sub_splits(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    split_chars_match = re_next_word.match(rest_of_op)
    raw_split_chars = split_chars_match.group(0)
    split_char = unescape(raw_split_chars)
    new_rest_of_op = rest_of_op[split_chars_match.end(0):].lstrip()
    return (new_rest_of_op,SubSplits(split_char))

def parse_replace(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    replace_filename_match = re_next_quoted_word.match(rest_of_op)
    replace_filename = replace_filename_match.group(0).strip("\"")
    new_rest_of_op = rest_of_op[replace_filename_match.end(0):].lstrip()
    return (new_rest_of_op,Replace(replace_filename))

def parse_discard_endings(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    endings_filename_match = re_next_quoted_word.match(rest_of_op)
    if not endings_filename_match:
        raise Exception("discard_endings: file name missing (did you forgot the quotes(\")?)")
    endings_filename = endings_filename_match.group(0).strip("\"")
    new_rest_of_op = rest_of_op[endings_filename_match.end(0):].lstrip()    
    return (new_rest_of_op,DiscardEndings(endings_filename))


macro_defs : Tuple[str,ComplexOperation] = { }

"""Mapping between the name of an op and it's associated parameters parser."""
operation_parsers = {

    "report": parse(REPORT),
    
    # FILTERS
    "max_length": parse_max_length,
    "min_length": parse_min_length,
    "is_regular_word" : parse(IS_REGULAR_WORD),
    "is_popular_word" : parse(IS_POPULAR_WORD),
    "is_pattern" : parse(IS_PATTERN),

    # EXTRACTORS
    "get_numbers": parse(GET_NUMBERS),
    "get_sc": parse(GET_SPECIAL_CHARS),
    "deduplicate" : parse(DEDUPLICATE),
    "detriplicate" : parse(DETRIPLICATE),

    # TRANSFORMERS
    "fold_ws": parse(FOLD_WHITESPACE),
    "lower": parse(LOWER),
    "upper": parse(UPPER),
    "remove_numbers": parse(REMOVE_NUMBERS),
    "remove_ws": parse(REMOVE_WHITESPACE),
    "remove_sc": parse(REMOVE_SPECIAL_CHARS),
    "capitalize" : parse(CAPITALIZE),
    "deleetify" : parse(DELEETIFY),
    "strip_ws" : parse(STRIP_WHITESPACE),
    "strip_numbers_and_sc" : parse(STRIP_NUMBERS_AND_SPECIAL_CHARS),
    "mangle_dates" : parse(MANGLE_DATES),
    "number": parse_number,
    "map": parse_map,
    "related": parse(RELATED),
    "split": parse_split,
    "sub_splits": parse_sub_splits,
    "replace" : parse_replace,
    "discard_endings" : parse_discard_endings,
    "correct_spelling" : parse(CORRECT_SPELLING),
}


def parse_rest_of_op(previous_ops : List[Operation], line_number, rest_of_op : str) -> Tuple[str, Operation]:
    # Get name of operation parser
    next_op_parser_match = re_next_word.match(rest_of_op)
    next_op_parser_name = next_op_parser_match.group(0)

    # Check for operation modifiers (i.e. Metaoperations)
    keep_always = (next_op_parser_name[0] == "+")                
    keep_if_filtered = (next_op_parser_name[0] == "*") 
    negate_filter = (next_op_parser_name[0] == "!") 
    if keep_always or keep_if_filtered or negate_filter:
        next_op_parser_name = next_op_parser_name[1:]

    result : Tuple[str, Operation] = None
    next_op_parser = operation_parsers.get(next_op_parser_name)
    if next_op_parser is not None:
        new_rest_of_op = rest_of_op[next_op_parser_match.end(
            0):].lstrip()
        result = next_op_parser(next_op_parser_name, new_rest_of_op)
    elif macro_defs.get(next_op_parser_name) is not None:
        macro_def = macro_defs.get(next_op_parser_name)
        new_rest_of_op = rest_of_op[next_op_parser_match.end(
            0):].lstrip()
        result = (
            new_rest_of_op,
            Macro(next_op_parser_name,macro_def.ops)
        )
    else:
        print(
            f"[error][{line_number}] unknown command: {next_op_parser_name}", 
            file=stderr
        )
        return None        

    if keep_always:
        (new_rest_of_op,base_op) = result
        result = (new_rest_of_op,KeepAlwaysModifier(base_op))
    elif keep_if_filtered:
        (new_rest_of_op,base_op) = result
        result = (new_rest_of_op,KeepOnlyIfFilteredModifier(base_op))
    elif negate_filter:
        (new_rest_of_op,base_op) = result
        result = (new_rest_of_op,NegateFilterModifier(base_op))

    return result
    

def parse_op(
        line_number : int, 
        is_def : bool, 
        sline : str
    ) -> ComplexOperation :
    # Parse a single operation definition in collaboration with the
    # respective atomic parsers.
    atomic_ops: List[Operation] = []
    while len(sline) > 0:
        parsed_atomic_op = parse_rest_of_op(atomic_ops, line_number, sline)
        if parsed_atomic_op:
            (sline, atomic_op) = parsed_atomic_op
            atomic_ops.append(atomic_op)
            if  not is_def and\
                len(sline) == 0 and\
                not (
                    isinstance(atomic_op,Report) 
                    or 
                    (   isinstance(atomic_op,Macro) 
                        and 
                        isinstance(atomic_op.ops[-1],Report)
                    )
                ):
                if _verbose:
                    print(f"[info][{line_number}] added missing report",  file=stderr)
                atomic_ops.append(Report())
        else:
            # If the parsing of an atomic operation fails, we just
            # ignore the line as a whole.
            print(f"[error][{line_number}] parsing failed: {sline}", file=stderr)
            return None

    return ComplexOperation(atomic_ops)


def parse_ops(ops_filename : str) -> List[ComplexOperation]:
    """ Parses operation definitions together with atomic operations parsers. 

        The split between the two kinds of parsers is as follows:
        This method parses global directives (`ignore`) and in all other
        cases it parses just the next word to determine the next atomic operation;
        the atomic operation is then responsible for parsing its parameters and
        removing them from the string.
    """

    ops: List[ComplexOperation] = []

    abs_filename = locate_resource(ops_filename)
    with open(abs_filename, 'r', encoding='utf-8') as ops_file:
        line_number = 0
        parsing_ops = False

        raw_lines = ops_file.readlines()
        effective_lines = []
        current_line = ""
        for i in range (len(raw_lines)-1,0-1,-1):
            raw_line = raw_lines[i].rstrip("\r\n")
            if raw_line.startswith('\ '):
                current_line = raw_line[2:] + " " + current_line
            else:
                effective_lines.append(raw_line + current_line)
                current_line = ""
        effective_lines.reverse()

        for op_def in effective_lines:
            line_number = line_number + 1
            sline = op_def.strip()

            # ignore comments and empty lines
            if sline.startswith('#') or len(sline) == 0:
                continue

            # parse ignore statement
            elif sline.startswith("ignore"):
                if parsing_ops:
                    raise IllegalStateError(
                        f"ignore statements ({sline}) have to be defined before operation definitions"
                    )

                filename = get_filename(sline[len("ignore")+1:].strip())
                abs_filename = locate_resource(filename)
                with open(abs_filename, 'r', encoding='utf-8') as fin:
                    for ignore_entry in fin:
                        # We want to be able to strip words with spaces
                        # at the beginning or end.
                        stripped_ignore_entry = ignore_entry.rstrip("\r\n")
                        if len(stripped_ignore_entry) > 0:
                            ignored_entries.add(stripped_ignore_entry)

            # parse macro definitions
            elif sline.startswith("def"):
                macro_def = sline[len("def")+1:]
                macro_name_match = re_next_word.match(macro_def)
                macro_name = macro_name_match.group(0)
                macro_body = macro_def[macro_name_match.end(0):].lstrip()
                if macro_name.upper() != macro_name:
                    raise ValueError(f"macro names need to be upper case: {macro_name}")
                op = parse_op(line_number, True, macro_body)
                if op:
                    if macro_defs.get(macro_name):
                        raise IllegalStateError(f"macro ({macro_name}) already defined")
                    else:
                        macro_defs[macro_name] = op

            # parse an operation definition
            else:
                parsing_ops = True
                op = parse_op(line_number, False, sline)
                if op:
                    ops.append(op)

    return ops


def transform_entries(
        dict_filename: str,
        ops: List[ComplexOperation]
    ):
    """Transforms the entries of a given dictionary."""
    d_in = None
    if dict_filename:
        d_in = open(dict_filename, 'r')
    else:
        d_in = sys.stdin
    
    count = 0
    for entry in d_in:
        count = count + 1
        sentry = entry.rstrip("\r\n") # stripped entry
        if sentry not in ignored_entries:
            _reported_entries.clear()
            for op in ops:
                if _verbose:
                    escaped_sentry = sentry\
                        .replace("\\","\\\\")\
                        .replace("\"","\\\"")
                    print(
                        f'[debug][{count}:"{escaped_sentry}"] applying: {op}',
                        file=stderr
                    )            
                op.apply(sentry)           


def main() -> int:
    global _verbose
    global _trace_ops

    parser = argparse.ArgumentParser(
        description=
        """Generates an attack dictionary based on a plain dictionary."""
    )
    parser.add_argument(
        '-o', 
        '--operations', 
        help="a .td file with the operations that will be applied to the dictionary entries", 
        default="default_ops.td"
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
    args = parser.parse_args()

    _verbose = args.verbose
    _trace_ops = args.trace_ops

    all_operations = parse_ops(args.operations)
    
    transform_entries(args.dictionary, all_operations)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())