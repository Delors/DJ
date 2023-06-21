#!/usr/bin/python3

# Dr. Michael Eichberg (mail@michael-eichberg.de)
# (c) 2022

import argparse
import sys
from parsimonious.grammar import Grammar
from parsimonious import NodeVisitor
from parsimonious.nodes import Node
# from abc import ABC, abstractmethod
# from importlib import import_module

from common import unescape

from dj_ast import ComplexOperation
from dj_ast import TDUnit, Body, Header, Comment
from dj_ast import Generate, IgnoreEntries, SetDefinition, GlobalSetDefinition
from dj_ast import MacroDefinition, ConfigureOperation, CreateFile
from dj_ops import NOP, REPORT, Write, Classify, MacroCall, Or, BreakUp
from dj_ops import IListIfAll, IListForeach, IListIfAny
from dj_ops import UseSet, StoreInSet, StoreFilteredInSet, StoreNotApplicableInSet, StoreFilteredAndNotApplicableInSet
from dj_ops import NegateFilterModifier, KeepAlwaysModifier, KeepOnlyIfNotApplicableModifier, KeepIfRejectedModifier
from operations.capitalize import CAPITALIZE
from operations.correct_spelling import CorrectSpelling
from operations.cut import Cut
from operations.dehex import DEHEX
from operations.deduplicate_reversed import DEDUPLICATE_REVERSED
from operations.deduplicate import DEDUPLICATE
from operations.deleetify import DELEETIFY
from operations.detriplicate import DETRIPLICATE
from operations.discard_endings import DiscardEndings
from operations.fold_ws import FOLD_WS
from operations.get_no import GET_NO
from operations.get_sc import GetSC
from operations.is_part_of import IsPartOf
from operations.is_pattern import IS_PATTERN
from operations.is_popular_word import IS_POPULAR_WORD
from operations.is_regular_word import IsRegularWord
from operations.is_sc import IsSC
from operations.is_walk import IsWalk
from operations.ilist_select_longest import ILIST_SELECT_LONGEST
from operations.ilist_unique import ISET_UNIQUE
from operations.lower import Lower
from operations.upper import Upper
from operations.rotate import Rotate
from operations.mangle_dates import MangleDates
from operations.map import Map
from operations.max import Max
from operations.ilist_max import IListMax
from operations.min import Min
from operations.has import Has
from operations.number import Number
from operations.pos_map import PosMap
from operations.related import Related
from operations.remove_ws import REMOVE_WS
from operations.remove_no import RemoveNO
from operations.remove_sc import RemoveSC
from operations.remove import Remove
from operations.replace import Replace
from operations.multi_replace import MultiReplace
from operations.reverse import REVERSE
from operations.segments import Segments
from operations.sieve import Sieve
from operations.strip_ws import STRIP_WS
from operations.strip_no import STRIP_NO
from operations.strip_sc import STRIP_SC
from operations.strip import Strip
from operations.split import Split
from operations.strip_no_and_sc import StripNOAndSC
from operations.sub_split import SubSplit
from operations.title import TITLE
from operations.swapcase import SWAPCASE
from operations.prepend import Prepend
from operations.append import Append
from operations.find_all import FindAll
from operations.omit import Omit
from operations.multiply import Multiply
from operations.glist_drop import GListDrop
from operations.glist_in import GListIn
from operations.ilist_concat import IListConcat


"""
Grammar of TD files. 

Please note, PEGs do greedy matching and therefore, e.g., "deduplicate_reversed" 
has to be defined in a PEG's or-group before "deduplicate". Otherwise,
"dedpulicate" would match the first part of "deduplicate_reversed"
and "_reversed" would then remain unmatched.
"""
DJ_GRAMMAR = Grammar(
    r"""    
    file            = header body 
    header          = ( ignore / set / global_set / config / def / gen / comment / create / _meaningless ) *
    body            = ( op_defs / comment / _meaningless ) +
    
    nl              = ~r"[\r\n]"m
    ws              = ~r"[ \t]"
    _meaningless    = ws* nl?
    continuation    = ( ~r"\s*\\\s*[\r\n]\s*"m ) / ws+ # In some cases it is possible to split a definition/sequence over multiple lines using "\" at the end.
    nl_continuation = ( ~r"\s*\\\s*[\r\n]\s*"m ) / ~r"\s*"s 
    comment         = ~r"#[^\r\n]*"    
    #quoted_string   = ~'"[^"]*"' # does not support escapes
    quoted_string   = ~r'"(?:(?:(?!(?<!\\)").)*)"' # supports nested escaped "
    file_name       = quoted_string
    identifier      = ~r"[A-Z_][A-Z0-9_]*" # we require identifiers of sets and macros to use capital letters to make them easily distinguishable
    op_operator     = ~r"[a-z_]+"
    float_value     = ~r"[0-9]+(\.[0-9]+)?"
    int_value       = ~r"[0-9][0-9]*"
    boolean_value   = "True" / "False"
    python_identifier = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
    #python_value    = ~r"[a-zA-Z0-9._+\[\]\",]+" # we also support simple lists of strings
    python_value    = ~r"[^\n\r]+" # we also support simple lists of strings

    ignore          = "ignore" ws+ file_name
    set             = "set" ws+ identifier
    global_set      = "global_set" ws+ identifier ws+ file_name( ~r"\(\s*"s op_defs ~r"\s*\)"s )?
    config          = "config" ws+ python_identifier ws+ python_identifier ws+ python_value
    def             = "def" ws+ identifier continuation op_defs
    gen             = "gen" ws+ ("alt") ws+ python_value
    create          = "create" ws+ file_name (ws* "<" ws* quoted_string)?

    op_defs         = op_modifier? op_def (continuation op_defs)* 

    # the op_modifier "!" can only be used with filters;
    # the op_modifiers "+", "*" and "~" can only be used with transformers/extractors
    op_modifier     = "+" / "*" / "!" / "~"
    
    # IN THE FOLLOWING THE ORDER OF OP DEFINITION MAY MATTER!
    op_def          = macro_call /
                      set_store /
                      set_use /
                      or /
                      ilist_if_all /
                      ilist_foreach /
                      ilist_if_any /
                      ilist_select_longest /
                      ilist_unique /
                      ilist_concat /
                      glist_drop /
                      glist_in /
                      break_up /
                      nop /
                      report /
                      write /
                      classify /
                      min /
                      max /
                      ilist_max /
                      has /
                      is_sc /
                      is_pattern /
                      is_walk /
                      is_part_of /
                      is_regular_word /
                      is_popular_word /
                      sieve /
                      find_all /
                      get_no /
                      get_sc /
                      cut /
                      dehex /
                      deduplicate_reversed /
                      deduplicate /                      
                      detriplicate /
                      segments /
                      strip_ws /
                      fold_ws /
                      rotate /
                      lower /
                      upper /
                      title /
                      swapcase /
                      capitalize /
                      remove_ws /
                      remove_no /
                      remove_sc /
                      remove /
                      strip /
                      strip_no_and_sc /
                      strip_sc /
                      strip_no /
                      reverse /
                      replace /
                      multi_replace /
                      omit /
                      map /
                      pos_map /
                      append /
                      prepend /
                      multiply /
                      split /
                      sub_split /
                      number /
                      discard_endings /
                      mangle_dates /                      
                      deleetify /
                      related /
                      correct_spelling 

    # Core operators                  
    # ======================================
    nop             = "_"
    macro_call      = "do" ws+ identifier
    # Handling of (intermediate) sets
    set_store       = "{" nl_continuation? op_defs nl_continuation? ( "}>" / "}[]>" / "}/>" / "}/[]>" ) ws* identifier
    set_use         = "use" (ws+ identifier)+ # a set use always has to be the first op in an op_defs
    # Meta operators that are set related
    ilist_if_all     = ~r"ilist_if_all\s*\(\s*" (~r"N/A\s*=\s*" boolean_value ~r"\s*,\s*\[\]\s*=\s*" boolean_value ~r"\s*,\s*")? op_defs ~r"\s*,\s*" op_defs ~r"\s*\)"s
    ilist_if_any     = ~r"ilist_if_any\s*\(\s*" (~r"N/A\s*=\s*"s boolean_value ~r"\s*,\s*\[\]\s*=\s*"s boolean_value ~r"\s*,\s*"s)? op_defs ~r"\s*\)"s
    ilist_foreach    = ~r"ilist_foreach\s*\(\s*" op_defs ~r"\s*\)"s    
    or              = ~r"or\s*\(\s*" op_defs ( ~r"\s*,\s*" op_defs )+ ~r"\s*\)"s
    break_up        = ~r"break_up\s*\(\s*" op_defs ~r"\s*\)"s
    # Reporting operators   
    report          = "report"
    write           = "write" ws+ file_name
    classify        = "classify" ws+ quoted_string

    # Modularized operators
    # ======================================
    # 1. FILTERS    
    min             = "min" ws+ op_operator ws+ int_value
    max             = "max" ws+ op_operator ws+ int_value
    ilist_max        = "ilist_max" ws+ op_operator ws+ int_value
    has             = "has" ws+ op_operator ws+ int_value
    is_sc           = "is_sc"    
    is_pattern      = "is_pattern"
    is_walk         = "is_walk" ws+ quoted_string
    is_part_of      = "is_part_of" ws+ quoted_string
    is_regular_word = "is_regular_word"
    is_popular_word = "is_popular_word"
    sieve           = "sieve" ws+ file_name
    ilist_select_longest  = "ilist_select_longest"
    ilist_unique     = "ilist_unique"
    # 2. EXTRACTORS
    find_all        = "find_all" (ws+ "join")? ws+ quoted_string
    get_no          = "get_no"
    get_sc          = "get_sc"
    cut             = "cut" ws+ ("l" / "r") ws+ int_value ws+ int_value
    dehex           = "dehex"
    deduplicate_reversed = "deduplicate_reversed"
    deduplicate     = "deduplicate"    
    detriplicate    = "detriplicate"
    segments        = "segments" ws+ int_value ws+ int_value   
    # 3. TRANSFORMERS
    strip_ws        = "strip_ws"
    fold_ws         = "fold_ws"
    rotate          = "rotate" ws+ int_value
    lower           = "lower" (ws+ int_value)?
    upper           = "upper" (ws+ "l"? int_value)?
    title           = "title"
    swapcase        = "swapcase"
    capitalize      = "capitalize"
    remove_ws       = "remove_ws"
    remove_no       = "remove_no"
    remove_sc       = "remove_sc"
    remove          = "remove" ws+ quoted_string
    strip           = "strip" ws+ quoted_string
    strip_no_and_sc = "strip_no_and_sc"    
    strip_no        = "strip_no"    
    strip_sc        = "strip_sc"    
    reverse         = "reverse"
    replace         = "replace" ws+ file_name    
    multi_replace   = "multi_replace" ws+ file_name    
    omit            = "omit" ws+ int_value
    map             = "map" (ws+ "not")? ws+ quoted_string ws+ quoted_string
    pos_map         = "pos_map" ws+ quoted_string
    multiply        = "multiply" ws+ int_value
    append          = "append" (ws+ "each")? ws+ quoted_string
    prepend         = "prepend" (ws+ "each")? ws+ quoted_string
    split           = "split" ws+ quoted_string
    sub_split       = "sub_split" ws+ quoted_string
    number          = "number" ws+ quoted_string   
    discard_endings = "discard_endings" ws+ file_name 
    mangle_dates    = "mangle_dates"    
    deleetify       = "deleetify"    
    related         = "related" ws+ float_value    
    correct_spelling = "correct_spelling"
    ilist_concat     = "ilist_concat" (ws+ quoted_string)?
    glist_drop       = "glist_drop" ws+ identifier
    glist_in         = "glist_in" ws+ identifier
    """
)


class DJTreeVisitor (NodeVisitor):
    # Note that this is a bottom-up visitor.

    def generic_visit(
        self, node, visited_children): return visited_children or node

    def visit_comment(self, node, _children): return Comment(node.text)
    def visit__meaningless(self, _node, _children): return None

    def visit_file(self, _node, children): (
        h, b) = children; return TDUnit(h, b)

    def visit_header(self, _node, children):
        # unwrapped_children = map(lambda x : x[0],children)
        # return Header([ o for o in unwrapped_children if o is not None ])
        return Header(list(c[0] for c in children if c[0] is not None))

    def visit_body(self, _node, children):
        # unwrapped_children = map(lambda x : x[0],children)
        # return Body([ o for o in unwrapped_children if o is not None ])
        return Body(list(c[0] for c in children if c[0] is not None))

    def visit_identifier(self, node, _): return node.text
    def visit_op_operator(self, node, _): return node.text
    def visit_float_value(self, node, _): return float(node.text)
    def visit_int_value(self, node, _): return int(node.text)

    def visit_boolean_value(self, node, _):
        return False if node.text == "False" else True

    def visit_python_identifier(self, node, _): return node.text
    def visit_python_value(self, node, _): return node.text

    def visit_quoted_string(self, node, _children):
        raw_text = node.text
        return unescape(raw_text[1:len(raw_text)-1])

    def visit_gen(_, node, children):
        (_gen, _ws, mode, _ws, value) = children
        return Generate(mode.text, value)

    def visit_ignore(self, _node, children):
        (_ignore, _ws, filename) = children
        return IgnoreEntries(filename)

    def visit_global_set(self, node, children):
        (_global_set, _ws, name, _ws, filename, op_defs_opt) = children
        op_defs = None
        if isinstance(op_defs_opt, list):
            (_ws, op_defs, _ws) = op_defs_opt[0]
        return GlobalSetDefinition(name, filename, op_defs)

    def visit_set(self, node, children):
        (_set, _ws, name) = children
        return SetDefinition(name)

    def visit_create(self, node, children):
        (_create, _ws, filename, initial_value) = children
        if isinstance(initial_value, list):
            (_ws, _, _ws, v) = initial_value[0]
            return CreateFile(filename, unescape(v))
        else:
            return CreateFile(filename, "")

    def visit_config(self, node, children):
        (_config, _ws, module_name, _ws, field_name, _ws, value) = children
        return ConfigureOperation(module_name, field_name, value)

    def visit_def(self, _node, visited_children):
        (_def, _ws, identifier, _ws, op_defs) = visited_children
        return MacroDefinition(identifier, op_defs)

    def visit_op_defs(self, node, visited_children):
        (raw_op_modifier, [op_def], raw_child_op_defs) = visited_children

        if isinstance(op_def, Node):
            raise NotImplementedError(
                f"visit method missing for {op_def.text}?")

        if isinstance(raw_op_modifier, list):
            op_modifier = raw_op_modifier[0][0].text
            if op_modifier == "+":
                op_def = KeepAlwaysModifier(op_def)
            elif op_modifier == "*":
                op_def = KeepOnlyIfNotApplicableModifier(op_def)
            elif op_modifier == "!":
                op_def = NegateFilterModifier(op_def)
            elif op_modifier == "~":
                op_def = KeepIfRejectedModifier(op_def)

        op_defs = [op_def]
        # lift the subsequent nodes/operations to a list
        if isinstance(raw_child_op_defs, list):
            next_ops = raw_child_op_defs[0][1].ops
            op_defs.extend(next_ops)
        else:  # [actually it is:] "elif isinstance(raw_child_op_defs,Node):"
            if len(raw_child_op_defs.children) > 0:
                (_ws, next) = raw_child_op_defs
                op_defs.extend(next.ops)

        return ComplexOperation(op_defs)

    def visit_macro_call(self, node, visited_children):
        (_do, _ws, identifier) = visited_children
        return MacroCall(identifier)

    def visit_set_store(self, node, visited_children):
        (_para, _ws, op_defs, _ws, [store_op],
         _ws, identifier) = visited_children
        op = store_op.text
        if op == "}>":
            return StoreInSet(identifier, op_defs)
        elif op == "}[]>":
            return StoreFilteredInSet(identifier, op_defs)
        elif op == "}/>":
            return StoreNotApplicableInSet(identifier, op_defs)
        else: # op == "}/[]>"
            return StoreFilteredAndNotApplicableInSet(identifier, op_defs)

    def visit_set_use(self, node, visited_children):
        (_use, raw_identifiers) = visited_children
        identifiers = list(map(lambda x: x[1], raw_identifiers))
        return UseSet(identifiers)

    def visit_or(self, node, visited_children):
        (_or_ws, cop, more_cops, _ws) = visited_children
        # more_cops is a list of tuples where the second tuple
        # value is the complex operation
        cops = map(lambda x: x[1], more_cops)  # strip "ws" nodes
        all_cops = [cop]
        all_cops.extend(cops)
        return Or(all_cops)

    def visit_ilist_foreach(self, n, visited_children):
        (_, cop, _) = visited_children
        return IListForeach(cop)

    def visit_ilist_if_all(self, n, visited_children):
        (_, on_none_and_on_empty, cop, _, test, _) = visited_children
        try:            
            [(_,on_none,_,on_empty,_)] = on_none_and_on_empty
            return IListIfAll(on_none,on_empty,cop,test)
        except Exception as e:
            return IListIfAll(False, False, cop, test)

    def visit_ilist_if_any(self, node, visited_children):
        (_, on_none_and_on_empty, cop, _) = visited_children
        try:            
            [(_,on_none,_,on_empty,_)] = on_none_and_on_empty
            return IListIfAny(on_none, on_empty, cop)
        except Exception as e:
            return IListIfAny(False, False, cop)

    def visit_break_up(self, n, visited_children):
        (_, test, _) = visited_children
        return BreakUp(test)

    def visit_nop(self, node, _children): return NOP
    def visit_report(self, node, _children): return REPORT

    def visit_write(self, node, children):
        (_write, _ws, filename) = children
        return Write(filename)
    
    def visit_classify(self, node, children):
        (_classify,_ws,classifier) = children
        return Classify(classifier)

    # IN THE FOLLOWING:
    #       "n" stands for Node and
    #       "c" stands for the visited children
    #       "_" is used for things that are not relevant
    def visit_min(self, _n, c): (_, _, op, _, v) = c; return Min(op, v)
    def visit_max(self, _n, c): (_, _, op, _, v) = c; return Max(op, v)
    def visit_ilist_max(self, _n, c): (_, _, op, _, v) = c; return IListMax(op, v)
    def visit_has(self, _n, c): (_, _, op, _, v) = c; return Has(op, v)
    def visit_is_sc(self, _n, _c): return IsSC()
    def visit_is_part_of(self, _n, c): (_, _, seq) = c; return IsPartOf(seq)
    def visit_is_pattern(self, _n, _c): return IS_PATTERN
    def visit_is_walk(self, _n, c): (_, _, k) = c; return IsWalk(k)
    # IsRegularWord is configurable; hence "on-demand" initialization is required
    def visit_is_regular_word(self, _n, _c): return IsRegularWord()
    def visit_is_popular_word(self, _n, _c): return IS_POPULAR_WORD
    def visit_sieve(self, _n, c): (_, _, f) = c; return Sieve(f)
    def visit_ilist_select_longest(self, _n, _c): return ILIST_SELECT_LONGEST
    def visit_ilist_unique(self, _n, _c): return ISET_UNIQUE

    def visit_find_all(self, _n, c):
        # The following test is really awkward, but I didn't find a
        # simpler solution to just test for the presence of this flag...
        (_, join, _, r) = c
        if isinstance(join, list):
            return FindAll(True, r)
        else:
            return FindAll(False, r)

    def visit_get_no(self, _n, _c): return GET_NO
    def visit_get_sc(self, _n, _c): return GetSC()

    def visit_cut(self, _n, c):
        # "cut" ws "l|r" ws <min> ws <max>
        (_, _, [op], _, min, _, max) = c
        return Cut(op.text, min, max)

    def visit_dehex(self, _n, _c): return DEHEX
    def visit_deduplicate_reversed(self, _n, _c): return DEDUPLICATE_REVERSED
    def visit_deduplicate(self, _n, _c): return DEDUPLICATE
    def visit_detriplicate(self, _n, _c): return DETRIPLICATE
    def visit_segments(self, _n, c): (
        _, _, min, _, max) = c; return Segments(min, max)

    def visit_strip_ws(self, _n, _c): return STRIP_WS
    def visit_strip_no(self, _n, _c): return STRIP_NO
    def visit_strip_sc(self, _n, _c): return STRIP_SC    
    def visit_fold_ws(self, _n, _c): return FOLD_WS
    def visit_rotate(self, _n, c): (_, _, by) = c; return Rotate(by)

    def visit_lower(self, _n, c):
        try:
            (_, [(_, pos)]) = c
            return Lower(pos)
        except:
            return Lower()

    def visit_upper(self, _n, c):
        try:
            (_, [(_, l_opt, pos)]) = c
            if isinstance(l_opt, list):
                return Upper(pos, letter_with_index=True)
            else:
                return Upper(pos)
        except:
            return Upper()

    def visit_title(self, _n, _c): return TITLE
    def visit_swapcase(self, _n, _c): return SWAPCASE
    def visit_capitalize(self, _n, _c): return CAPITALIZE
    def visit_remove_ws(self, _n, _c): return REMOVE_WS
    def visit_remove_no(self, _n, _c): return RemoveNO()
    def visit_remove_sc(self, _n, _c): return RemoveSC()
    def visit_remove(self, _n, c): (_, _, cs) = c; return Remove(cs)
    def visit_strip(self, _n, c): (_, _, cs) = c; return Strip(cs)
    def visit_strip_no_and_sc(self, _n, _c): return StripNOAndSC()
    def visit_reverse(self, _n, _c): return REVERSE
    def visit_replace(self, _n, c): (_, _, f) = c; return Replace(f)
    def visit_multi_replace(self, _n, c): (_, _, f) = c; return MultiReplace(f)
    def visit_omit(self, _n, c): (_, _, v) = c; return Omit(v)    
    def visit_pos_map(self, _n, c): (_, _, pm) = c; return PosMap(pm)
    def visit_map(self, _n, c): 
        (_map_op, map_not, _, srcs, _, trgts) = c
        return Map(isinstance(map_not,list), srcs, trgts)

    def visit_append(self, _n, c):
        (_, m, _, s) = c
        # The following test is really awkward, but I didn't find a
        # simpler solution to just test for the presence of this flag...
        return Append(isinstance(m, list), s)

    def visit_prepend(self, _n, c):
        (_, m, _, s) = c
        # The following test is really awkward, but I didn't find a
        # simpler solution to just test for the presence of this flag...
        return Prepend(isinstance(m, list), s)

    def visit_ilist_concat(self, _n, c):
        (_, s_opt) = c
        if isinstance(s_opt, list):
            return IListConcat(s_opt[0][1])
        else:
            return IListConcat("")

    def visit_multiply(self, _n, c): (_, _, f) = c; return Multiply(f)
    def visit_split(self, _n, c): (_, _, s) = c; return Split(s)
    def visit_sub_split(self, _n, c): (_, _, s) = c; return SubSplit(s)
    def visit_number(self, _n, c): (_, _, cs) = c; return Number(cs)
    def visit_discard_endings(self, _n, c): (
        _, _, f) = c; return DiscardEndings(f)

    def visit_mangle_dates(self, _n, _c): return MangleDates()
    def visit_deleetify(self, _n, _c): return DELEETIFY
    def visit_related(self, _n, c): (_, _, r) = c; return Related(r)
    def visit_correct_spelling(self, _n, _c): return CorrectSpelling()

    def visit_glist_drop(_, node, children):
        (_glist_drop, _ws, setname) = children
        return GListDrop(setname)

    def visit_glist_in(_, node, children):
        (_glist_in, _ws, setname) = children
        return GListIn(setname)


DJ_EXAMPLE_FILE = """
# This is just a demo file that demonstrates technical possibilities;
# it does not implement useful transformations as such.

ignore "ignore/de.txt"

config related K 15
config related KEEP_ALL_RELATEDNESS 0.777

set NO_PATTERN
set WALK
set RELATED
set NO_WORD

def BASE_TRANSFORMATIONS \
 *strip_no_and_sc \
 !is_pattern \
 *replace "replace/SpecialCharToSpace.txt" \
 *split " " \
 *sub_split "-" \
 *strip_ws \
 *fold_ws \
 +deduplicate \
 min length 3 \
 *deleetify

+related 0.5 min length 3 
do BASE_TRANSFORMATIONS 

{ is_walk "PIN_PAD" }> WALK
{ is_pattern }[]> NO_PATTERN 

{ or(is_walk "KEYBOARD_DE" , is_pattern, is_sc) }> NO_WORD

{ *split "\\"" \
    ilist_foreach( 
        *strip_ws \
        *fold_ws \
        related 0.5 ) }> RELATED

use NO_PATTERN WALK map "s" "abc\\n\\r\\t" report
"""

DJ_SIMPLE_EXAMPLE_FILE = """
*strip_ws fold_ws report
"""


def main():
    parser = argparse.ArgumentParser(
        description="""Reads and prints a DJ file - intended for debugging purposes."""
    )
    parser.add_argument(
        '-o',
        '--operations',
        help="a .dj file with the specified operations"
    )
    args = parser.parse_args()
    if args.operations:
        with open(args.operations, mode="r") as f:
            dj_file = f.read()
    else:
        # dj_file = DJ_SIMPLE_EXAMPLE_FILE
        dj_file = DJ_EXAMPLE_FILE

    print("\nSource:")
    print("=====================================================================")
    tree = DJ_GRAMMAR.parse(dj_file)

    print("\nSyntaxtree:")
    print("=====================================================================")
    print(tree)

    print("\nAST:")
    print("=====================================================================")
    td_unit: TDUnit = DJTreeVisitor().visit(tree)
    print(td_unit)

    print("\nInitialization:")
    print("=====================================================================")
    td_unit.verbose = True
    td_unit.init(td_unit, None)


if __name__ == '__main__':
    sys.exit(main())
