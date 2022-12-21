#!/usr/bin/python3

# Dr. Michael Eichberg (mail@michael-eichberg.de)
# (c) 2022

import sys
from sys import stderr
import os
import argparse
import re
import importlib
import traceback

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

from common import IllegalStateError,escape,unescape,get_filename,locate_resource,enrich_filename

from operations.operation import Operation
# TRANSFORMERS
from operations.deleetify import DELEETIFY
from operations.remove_ws import REMOVE_WS
from operations.capitalize import CAPITALIZE
from operations.lower import LOWER
from operations.upper import UPPER
from operations.fold_ws import FOLD_WS
from operations.remove_no import REMOVE_NO
from operations.remove_sc import REMOVE_SC
from operations.strip_ws import STRIP_WS
from operations.strip_no_and_sc import STRIP_NO_AND_SC
from operations.mangle_dates import MANGLE_DATES
from operations.replace import Replace
from operations.map import Map
from operations.pos_map import PosMap
from operations.split import Split
from operations.sub_split import SubSplit
from operations.discard_endings import DiscardEndings
from operations.number import Number
from operations.correct_spelling import CORRECT_SPELLING
from operations.related import Related
from operations.reverse import REVERSE
# EXTRACTORS
from operations.get_no import GET_NO
from operations.get_sc import GET_SC
from operations.deduplicate import DEDUPLICATE
from operations.detriplicate import DETRIPLICATE
from operations.deduplicate_reversed import DEDUPLICATE_REVERSED
from operations.segments import Segments
# FILTERS
from operations.min import Min
from operations.is_regular_word import IS_REGULAR_WORD
from operations.is_popular_word import IS_POPULAR_WORD
from operations.is_pattern import IS_PATTERN
from operations.is_walk import IsWalk
from operations.is_sc import IS_SC
from operations.sieve import Sieve


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

sets : Tuple[str,List[str]] = {}
""" The sets which are created while processing the entries. The
    sets are cleared whenever a new dictionary entry is analyzed.
"""

def _clear_sets():
    for k in sets.keys(): sets[k] = []


def apply_ops(entry : str, ops : List[Operation]) -> List[str]:
    """ Applies all operations to the given entry. As a result multiple new 
        entries may be generated. None is returned if and only if the 
        application of an operation to all (intermediate) entries resulted in 
        `None`. (cf. Operation.processEntries)
    """

    entries = [entry]    
    for op in ops:
        if _trace_ops:
            print(f"[trace] {op}({entries})",file=stderr)

        try:
            new_entries = op.process_entries(entries)
        except Exception as e:
            print(traceback.format_exc())
            print(f"[error] {op}({entries}) failed: {str(e)}",file=stderr)              
            return

        if _trace_ops:
            print(f"[trace] result:   {new_entries}",file=stderr)

        if new_entries is None:
            return None

        entries = []
        for new_entry in new_entries:
            if len(new_entry) == 0:
                continue
            if new_entry in ignored_entries:
                if _trace_ops:
                    print(f"[trace] ignoring: {new_entry}")
            else:
                entries.append(new_entry)

        if len(entries) == 0:
            return []

    return entries


class ComplexOperation:
    """ Representation of a complex operation.

        Instantiation of a complex operation which is made up of 
        multiple atomic/macro operations. An instance of ComplexOperation 
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

    def close(self):
        for op in self.ops: op.close()

    def __str__(self) -> str:
        return " ".join(map(str,self.ops))


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

    def op_name() -> str: return "report"

    def is_reporter(self) -> bool: return True   

    def process(self, entry: str) -> List[str]:
        report(entry)
        return [entry]


REPORT = Report()        


class Write(Report):

    def op_name() -> str: return "write"

    def __init__(self,filename) -> None:
        super().__init__()
        self.filename = filename
        self.file = open(enrich_filename(filename),"w",encoding="utf-8")

    def is_reporter(self) -> bool: return True   

    def process(self, entry: str) -> List[str]:
        print(entry,file=self.file)
        return [entry]

    def close(self):
        try:
            self.file.close()
        except Exception as e:
            print(f"failed closing {self.filename}",file=stderr)
            pass
               
    def __str__(self):
        return f"{Write.op_name()} \"{self.filename}\""



class Use(Operation):

    def op_name() -> str: return "use"

    def __init__(self,setname) -> None:
        super().__init__()
        self.setname = setname

    def process(self, entry: str) -> List[str]:
        return sets[self.setname]
               
    def __str__(self):
        return f"{Use.op_name()} {self.setname}" 

class StoreInSet(Operation):

    def op_name() -> str: return "store_in"

    def __init__(self,setname,ops : ComplexOperation) -> None:
        super().__init__()
        self.setname = setname
        self.ops = ops

    def process(self, entry: str) -> List[str]:
        return entry
               
    def __str__(self):
        return f"{StoreInSet.op_name()} {self.setname}({self.ops})" 


class StoreFilteredInSet(Operation):

    def op_name() -> str: return "store_filtered_in"

    def __init__(self,setname,ops : ComplexOperation) -> None:
        super().__init__()
        self.setname = setname
        self.ops = ops

    def process(self, entry: str) -> List[str]:
        return entry
               
    def __str__(self):
        return f"{StoreFilteredInSet.op_name()} {self.setname}({self.ops})" 



class MacroCall(Operation):
    """Represents a macro call."""

    def op_name() -> str: return "do"

    def __init__(self, name :str, ops : List[Operation]): # TODO set ops in init step
        self.name = name
        self.ops = ops
        return

    def is_macro(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        return apply_ops(entry,self.ops)

    def close(self):
        for op in self.ops: op.close()    

    def __str__(self):
        return f"{MacroCall.op_name()} {self.name}"


class KeepAlwaysModifier(Operation):
    """ Modifies the behavior of the wrapped transformer/extractor
        such that all input entries will also be output entries 
        additionally to those that are newly created by the 
        wrapped operation.
    """

    def op_name() -> str: return "+"

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
        return KeepAlwaysModifier.op_name() + str(self.op)


class KeepOnlyIfFilteredModifier(Operation):
    """ Modifies the behavior of the wrapped operation such that an
        input entry will be an output entry if the wrapped operation
        does not apply to the entry. I.e., if the wrapped operation 
        returns None, the entry is passed on otherwise the result
        of the wrapped operation is passed on as is.
    """

    def op_name() -> str: return "*"

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
        return KeepOnlyIfFilteredModifier.op_name() + str(self.op)        


class NegateFilterModifier(Operation):
    """ Modifies the behavior of the wrapped filter such that if the 
        given entry is returned by the underlying filter, an empty 
        list will be returned and vice versa.
    """

    def op_name() -> str : return "!"

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
        return NegateFilterModifier.op_name() + str(self.op)        

class Or(Operation):

    def op_name() -> str : return "or"

    def __init__(self, cops : List[ComplexOperation]) -> None:
        self.cops = cops

    def __str__(self):
        cops = ", ".join(map (lambda x: str(x), self.cops))
        return Or.op_name() +"(" + cops + ")"

### PARSER SETUP AND CONFIGURATION

re_next_float = re.compile("^[0-9]+\.?[0-9]*")
re_next_word = re.compile("^[^\s]+")
# OLD: re_next_quoted_word = re.compile('^"[^"]+"')
re_next_quoted_word = re.compile(r'^"(?:\\.|[^\\])*?"') # supports escapes
re_next_char_set = re.compile(r'^\[(?:\\.|[^\\])*?\]') # supports escapes


def parse(operation) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations without parameters."""

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        return (rest_of_op,operation)

    return parse_it   

def parse_only_static_parameters(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations without a parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        return (rest_of_op,operation_constructor())

    return parse_it

def parse_int_parameter(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations with a single int parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        int_match = re_next_word.match(rest_of_op)
        if not int_match:
           raise Exception(f"{op_name}: int parameter missing") 
        try:   
            raw_value = int_match.group(0)
            value = int(raw_value)
        except ValueError as ve:
            raise Exception(f"{op_name}: parameter {raw_value} is not an int") 
        new_rest_of_op = rest_of_op[int_match.end(0):].lstrip()
        return (new_rest_of_op,operation_constructor(value))

    return parse_it

def parse_float_parameter(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations with a single float parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        float_match = re_next_float.match(rest_of_op)
        if not float_match:
           raise Exception(f"{op_name}: float parameter missing") 
        try:   
            raw_value = float_match.group(0)
            value = float(raw_value)
        except ValueError as ve:
            raise Exception(f"{op_name}: parameter {raw_value} is not a float") 
        new_rest_of_op = rest_of_op[float_match.end(0):].lstrip()
        return (new_rest_of_op,operation_constructor(value))

    return parse_it

def parse_string(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations with a single unquoted string parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        string_match = re_next_word.match(rest_of_op)
        if not string_match:
           raise Exception(f"{op_name}: string parameter missing") 
        value = string_match.group(0)
        new_rest_of_op = rest_of_op[string_match.end(0):].lstrip()
        return (new_rest_of_op,operation_constructor(value))

    return parse_it

def parse_quoted_string(operation_constructor):
    """Generic parser for operations with a quoted parameter."""
    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        string_match = re_next_quoted_word.match(rest_of_op)
        if not string_match:
            raise Exception(f"{op_name}: empty match (did you forgot the quotes?)")
        string = string_match.\
            group(0).\
            strip("\"").\
            replace("\\\"","\"").\
            replace("\\\\","\\")
        new_rest_of_op = rest_of_op[string_match.end(0):].lstrip()        
        return (new_rest_of_op,operation_constructor(string))    

    return parse_it

def parse_number(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    chars_to_number_match = re_next_word.match(rest_of_op)
    raw_chars_to_number = chars_to_number_match.group(0)
    chars_to_number = unescape(raw_chars_to_number)
    new_rest_of_op = rest_of_op[chars_to_number_match.end(0):].lstrip()
    return (new_rest_of_op,Number(chars_to_number[1:-1] ))


def parse_map(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    source_char_match = re_next_word.match(rest_of_op)
    raw_source_char = source_char_match.group(0)
    source_char = unescape(raw_source_char)
    rest_of_op = rest_of_op[source_char_match.end(0):].lstrip()

    target_chars_match = re_next_word.match(rest_of_op)
    raw_target_chars = target_chars_match.group(0)
    target_chars = unescape(raw_target_chars)
    new_rest_of_op = rest_of_op[target_chars_match.end(0):].lstrip()

    # TODO make parse set...
    return (new_rest_of_op,Map(source_char,target_chars[1:-1]))    

def parse_min(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    min_op_match = re_next_word.match(rest_of_op)
    raw_min_op = min_op_match.group(0)
    min_op = unescape(raw_min_op)
    rest_of_op = rest_of_op[min_op_match.end(0):].lstrip()

    int_match = re_next_word.match(rest_of_op)
    if not int_match:
        raise Exception(f"{op_name}: int parameter missing") 
    try:   
        raw_min_count = int_match.group(0)
        min_count = int(raw_min_count)
    except ValueError as ve:
        raise Exception(f"{op_name}: parameter {raw_min_count} is not an int") 
    rest_of_op = rest_of_op[int_match.end(0):].lstrip()
    return (rest_of_op,Min(min_op,min_count))    

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


macro_defs : Tuple[str,ComplexOperation] = { }


"""Mapping between the name of an op and it's associated parameters parser."""
operation_parsers = {

    "report" : parse(REPORT),
    "write" : parse_quoted_string(Write),
    
    # FILTERS
    "min" : parse_min,
    "is_regular_word" : parse(IS_REGULAR_WORD),
    "is_popular_word" : parse(IS_POPULAR_WORD),
    "is_pattern" : parse(IS_PATTERN),
    "is_walk" : parse_only_static_parameters(IsWalk),
    "is_sc" : parse(IS_SC),
    "sieve" : parse_quoted_string(Sieve),

    # EXTRACTORS
    "get_numbers" : parse(GET_NO),
    "get_sc" : parse(GET_SC),
    "deduplicate" : parse(DEDUPLICATE),
    "deduplicate_reversed" : parse(DEDUPLICATE_REVERSED),
    "detriplicate" : parse(DETRIPLICATE),
    "segments" : parse_int_parameter(Segments),

    # TRANSFORMERS
    "reverse" : parse(REVERSE),
    "fold_ws" : parse(FOLD_WS),
    "lower" : parse(LOWER),
    "upper" : parse(UPPER),
    "remove_numbers" : parse(REMOVE_NO),
    "remove_ws" : parse(REMOVE_WS),
    "remove_sc" : parse(REMOVE_SC),
    "capitalize" : parse(CAPITALIZE),
    "deleetify" : parse(DELEETIFY),
    "strip_ws" : parse(STRIP_WS),
    "strip_numbers_and_sc" : parse(STRIP_NO_AND_SC),
    "mangle_dates" : parse(MANGLE_DATES),
    "number" : parse_number,
    "map" : parse_map,
    "pos_map" : parse_quoted_string(PosMap),
    "related" : parse_float_parameter(Related),
    "split" : parse_split,
    "sub_splits" : parse_sub_splits,
    "replace" : parse_quoted_string(Replace),
    "discard_endings" : parse_quoted_string(DiscardEndings),
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

    if next_op_parser_name[0] == ">":
        if next_op_parser_name.startswith(">>"):
            set_name = next_op_parser_name[2:]
            store_filtered = False
        elif next_op_parser_name.startswith(">!>"):
            set_name = next_op_parser_name[3:]
            store_filtered = True
        else:
            print(
                f"[error][{line_number}] unsupported redirection command: {next_op_parser_name}", 
                file=stderr
            )
            return None
        if sets.get(set_name) is None:
            print(
                f"[error][{line_number}] unknown set: {set_name}", 
                file=stderr
            )
            return None
        new_rest_of_op = rest_of_op[next_op_parser_match.end(
                0):].lstrip()
        result = (new_rest_of_op, StoreInHeap(set_name,store_filtered))

    else:
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
            if  not is_def and \
                len(sline) == 0 and \
                not (
                    isinstance(atomic_op,Report) 
                    or 
                    (   # ... a macro with a report at the end!
                        isinstance(atomic_op,Macro) 
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


def parse_ops_file(ops_filename : str) -> List[ComplexOperation]:
    """ Parses a file containing operation definitions.
    """
    abs_filename = locate_resource(ops_filename)
    raw_lines : List[str] = []
    with open(abs_filename, 'r', encoding='utf-8') as ops_file:
        raw_lines = ops_file.readlines()

    return parse_ops(raw_lines)


def parse_ops(raw_lines : List[str]) -> List[ComplexOperation]:
    """ Parses operation definitions together with atomic operations parsers. 

        The split between the two kinds of parsers is as follows:
        This method parses global directives (`ignore`) and in all other
        cases it parses just the next word to determine the next atomic operation;
        the atomic operation is then responsible for parsing its parameters and
        removing them from the string.
    """
    ops: List[ComplexOperation] = []
    line_number = 0
    parsing_ops = False
    effective_lines = []
    current_line = ""
    for i in range (len(raw_lines)-1,0-1,-1):
        raw_line = raw_lines[i].rstrip("\r\n")
        if raw_line.startswith('\ '):
            current_line = raw_line[2:] + " " + current_line
        else:
            if len(current_line) > 0:
                effective_lines.append(raw_line + " " + current_line)
            else:
                effective_lines.append(raw_line)
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

        elif sline.startswith("set"):
            set_def = sline[len("set")+1:]            
            set_name_match = re_next_word.match(set_def)
            set_name = set_name_match.group(0)
            if set_name.upper() != set_name:
                raise ValueError(f"set names need to be upper case: {set_name}")
            if sets.get(set_name):
                raise IllegalStateError(f"set ({set_name}) already defined")
            else:
                sets[set_name] = {}     

        elif sline.startswith("config"):
            if parsing_ops:
                raise IllegalStateError(
                    f"config statements ({sline}) have to be defined before operation definitions"
                )

            raw_config = sline[len("config")+1:].split()
            if len(raw_config) != 3:
                raise ValueError(
                    f"invalid config: {raw_config} (expected format: <op-module> <field> <value>)"
                )
            (op_module_name,field_name,raw_value) = raw_config
            op_module = importlib.import_module("operations."+op_module_name)
            op_class_name = "".join(
                    map (lambda x: x.capitalize(), op_module_name.split("_"))
                )
            op_class = getattr(op_module,op_class_name)
            value = None
            try:
                old_value = getattr(op_class,field_name)
            except AttributeError:
                # we don't want to create "new" fields 
                raise ValueError(
                    f"unknown field name: {op_class_name}.{field_name}"
                )

            if _verbose:
                print(
                    f"[debug] config:"+
                    f"{op_module.__name__}.{op_class.__name__}.{field_name} = "+
                    f"{raw_value} (old:{old_value})",file=sys.stderr)


            value_type = type(old_value)
            if value_type == int:
                value = int(raw_value)
            elif value_type == bool:
                value = bool(raw_value)                
            elif value_type == float:
                value = float(raw_value)
            elif value_type == str:
                value = raw_value
            else:
                raise ValueError(
                    f"unknown type: {value_type}; expected: integer, float or strings"
                )
            setattr(op_class,field_name,value)


        # parse an operation definition
        else:
            parsing_ops = True
            try:
                op = parse_op(line_number, False, sline)
                if op:
                    ops.append(op)
            except ValueError as ve:
                print(
                    f"failed parsing:\n\t{sline}\n\t{ve.args[0]}\n\tparsing aborted",
                    file=sys.stderr
                )
                return []

    return ops


def transform_entries(
        dict_filename: str,
        ops: List[ComplexOperation],
        print_progress : bool
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
            if print_progress: 
                print(f"[progress] processing:",sentry,file=sys.stderr)           

            _reported_entries.clear()
            _clear_sets()
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
        else:
            if print_progress: 
                print(f"[progress] ignoring: {sentry}",file=sys.stderr)


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
        help="a .td file with the operations that will be applied to the dictionary entries"
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

    _verbose = args.verbose
    _trace_ops = args.trace_ops

    # 1. parse operations
    all_operations : List[ComplexOperation] = []
    if args.operations:
        all_operations.extend(parse_ops_file(args.operations))
    all_operations.extend(parse_ops([" ".join(args.adhoc_operations)]))

    # 2. apply operations
    if len(all_operations) == 0:
        print("no (valid) operations specified",file=sys.stderr)
    else:    
        transform_entries(args.dictionary, all_operations, args.progress)

    # 3. cleanup operations
    for op in all_operations: 
        op.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
