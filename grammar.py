#!/usr/bin/python3

# Dr. Michael Eichberg (mail@michael-eichberg.de)
# (c) 2022

import argparse
import sys
from parsimonious.grammar import Grammar
from parsimonious import NodeVisitor
from parsimonious.nodes import Node
from typing import List

from common import IllegalStateError, ValidationFailed, unescape
from operations.operation import Operation
from DJ import ComplexOperation
from DJ import REPORT, Write, MacroCall, Use, StoreInSet, StoreFilteredInSet, Or
from DJ import NegateFilterModifier, KeepAlwaysModifier, KeepOnlyIfFilteredModifier
from operations.capitalize import CAPITALIZE
from operations.correct_spelling import CORRECT_SPELLING
from operations.deduplicate_reversed import DEDUPLICATE_REVERSED
from operations.deduplicate import DEDUPLICATE
from operations.deleetify import DELEETIFY
from operations.detriplicate import DETRIPLICATE
from operations.discard_endings import DiscardEndings
from operations.fold_ws import FOLD_WS
from operations.get_no import GET_NO
from operations.get_sc import GET_SC
from operations.is_pattern import IS_PATTERN
from operations.is_popular_word import IS_POPULAR_WORD
from operations.is_regular_word import IS_REGULAR_WORD
from operations.is_sc import IS_SC
from operations.is_walk import IS_WALK
from operations.lower import LOWER
from operations.mangle_dates import MANGLE_DATES
from operations.map import Map
from operations.max import Max
from operations.min import Min
from operations.number import Number
from operations.pos_map import PosMap
from operations.related import Related
from operations.remove_no import REMOVE_NO
from operations.remove_sc import REMOVE_SC
from operations.remove_ws import REMOVE_WS
from operations.replace import Replace
from operations.reverse import REVERSE
from operations.segments import Segments
from operations.sieve import Sieve
from operations.strip_ws import STRIP_WS
from operations.split import Split
from operations.strip_no_and_sc import STRIP_NO_AND_SC
from operations.strip_ws import STRIP_WS
from operations.sub_split import SubSplit
from operations.upper import UPPER


"""
Grammar of TD files. 

Please note, PEGs do greedy matching and that, e.g., "deduplicate_reversed" 
has to be defined in a PEG's or-group before "deduplicate". Otherwise,
"dedpulicate" would match the first part of "deduplicate_reversed"
and "_reversed" would then remain unmatched.
"""
DJ_GRAMMAR = Grammar(
    r"""    
    file            = header body 
    header          = ( ignore / set / config / def / comment / _meaningless ) *
    body            = ( op_defs / comment / _meaningless ) +
    
    nl              = ~r"[\r\n]"m
    ws              = ~r"[ \t]"
    _meaningless    = ws* nl?
    continuation    = ( ~r"\s*\\[\r\n]\s+"m ) / ws+ # In some cases it is possible to split a definition/sequence over multiple lines using "\" at the end.
    comment         = ~r"#[^\r\n]*"    
    quoted_string   = ~'"[^"]*"' # TODO support quoted '"'
    file_name       = quoted_string
    identifier      = ~r"[A-Z_]+"a # Identifiers of sets and macros have to use capital letters to make the easily distinguishable
    op_operator     = ~r"[a-z]+"
    float_value     = ~r"[0-9]+(\.[0-9]+)?"
    int_value       = ~r"[1-9][0-9]*"
    python_identifier = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
    python_value    = ~r"[a-zA-Z0-9._]+"

    ignore          = "ignore" ws+ file_name
    set             = "set" ws+ identifier
    config          = "config" ws+ python_identifier ws+ python_identifier ws+ python_value
    def             = "def" ws+ identifier continuation op_defs

    op_defs         = op_modifier? op_def (continuation op_defs)* 

    # the op_modifier "!" can only be used with filters;
    # the op_modifiers "+" and "x" can only be used with transformers/extractors
    op_modifier     = "+" / "*" / "!"
    
    # IN THE FOLLOWING THE ORDER OF OP DEFINITION MAY MATTER!
    op_def          = macro_call /
                      set_store /
                      set_use /
                      or /
                      report /
                      write /
                      min /
                      max /
                      is_sc /
                      is_pattern /
                      is_walk /
                      is_regular_word /
                      is_popular_word /
                      sieve /
                      get_no /
                      get_sc /
                      deduplicate_reversed /
                      deduplicate /                      
                      detriplicate /
                      segments /
                      strip_ws /
                      fold_ws /
                      remove_ws /
                      lower /
                      upper /
                      capitalize /
                      remove_no /
                      remove_sc /
                      strip_no_and_sc /                      
                      reverse /
                      replace /
                      map /
                      pos_map /
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
    macro_call      = "do" ws+ identifier
    # Handling of (intermediate) sets
    set_store       = ( "store_in" / "store_filtered_in" ) ws+ identifier "(" continuation? op_defs continuation? ")"        
    set_use         = "use" ws+ identifier # a set use always has to be the first op in an op_defs
    # Meta operators that can only be combined with filters
    #or              = "or(" ws* op_defs (ws* "," ws* op_defs)+ ws* ")"
    or              = ~r"or\(\s*" op_defs ( ~r"\s*,\s*" op_defs )+ ~r"\s*\)"
    # Reporting operators
    report          = "report"
    write           = "write" ws+ file_name

    # Modularized operators
    # ======================================
    # 1. FILTERS    
    min             = "min" ws+ op_operator ws+ int_value
    max             = "max" ws+ op_operator ws+ int_value
    is_sc           = "is_sc"    
    is_pattern      = "is_pattern"
    is_walk         = "is_walk"
    is_regular_word = "is_regular_word"
    is_popular_word = "is_popular_word"
    sieve           = "sieve" ws+ file_name
    # 2. EXTRACTORS
    get_no          = "get_no"
    get_sc          = "get_sc"
    deduplicate_reversed = "deduplicate_reversed"
    deduplicate     = "deduplicate"    
    detriplicate    = "detriplicate"
    segments        = "segments" ws+ int_value   
    # 3. TRANSFORMERS
    strip_ws        = "strip_ws"
    fold_ws         = "fold_ws"
    remove_ws       = "remove_ws"
    lower           = "lower"
    upper           = "upper"
    capitalize      = "capitalize"
    remove_no       = "remove_no"
    remove_sc       = "remove_sc"
    strip_no_and_sc = "strip_no_and_sc"    
    reverse         = "reverse"
    replace         = "replace" ws+ file_name
    map             = "map" ws+ quoted_string ws+ quoted_string
    pos_map         = "pos_map" ws+ quoted_string
    split           = "split" ws+ quoted_string
    sub_split       = "sub_spit" ws+ quoted_string
    number          = "number" ws+ quoted_string   
    discard_endings = "discard_endings" ws+ file_name 
    mangle_dates    = "mangle_dates"    
    deleetify       = "deleetify"    
    related         = "related" ws+ float_value    
    correct_spelling = "correct_spelling"
    """
)

DJ_EXAMPLE_FILE = """
# This is just a demo file that demonstrates technical possibilities;
# it does not implement useful transformations as such.

ignore "ignore/de.txt"

config related K 15
config related KEEP_ALL_RELATEDNESS 0.75

set NO_PATTERN
set WALK
set RELATED
set NO_WORD

def BASE_TRANSFORMATIONS \
 *strip_no_and_sc \
 !is_pattern \
 *replace "replace/SpecialCharToSpace.txt" \
 *split " " \
 *strip_ws \
 *fold_ws \
 +deduplicate \
 min length 3 \
 *deleetify

+related 0.5 min length 3 
do BASE_TRANSFORMATIONS 

store_in WALKS(is_walk)
store_filtered_in NO_PATTERNS( is_pattern )

store_in NO_WORD(or(is_walk, is_pattern, is_sc ))

store_in RELATED( *split " " \
 *strip_ws \
 *fold_ws \
 related 0.5 )

use NO_PATTERNS map "s" "abc"
"""

DJ_SIMPLE_EXAMPLE_FILE="""
*strip_ws fold_ws report
"""

class ASTNode:

    def validate(self, spec : 'TDFile', parent : 'ASTNode'): 
        pass

    

class Comment:
    def __init__(self,comment):
        self.comment = comment
    def __str__(self):
        return self.comment

class SetupOperationNode(ASTNode):
    pass

class SetDefinition(SetupOperationNode):
    def __init__(self,name):
        self.name = name
    def __str__(self) -> str:
        return "set "+self.name

class IgnoreEntries(SetupOperationNode):
    def __init__(self,filename):
        self.filename = filename
    def __str__(self) -> str:
        return "ignore \""+self.filename+"\""

class ConfigureOperations(SetupOperationNode):
    def __init__(self,modulename,fieldname,fieldvalue):
        self.modulename = modulename
        self.fieldname = fieldname
        self.fieldvalue = fieldvalue
    def __str__(self):
        return \
            "config "+\
            self.modulename+" "+\
            self.fieldname+" "+\
            self.fieldvalue

class MacroDefinition(SetupOperationNode):
    def __init__(self,name,ops):
        self.name = name
        self.ops = ops
    def __str__(self) -> str:
        return "def "+self.name+" "+str(self.ops)

class Header(ASTNode):
    def __init__(self, setup_ops : List[SetupOperationNode]):
        unwrapped_setup_ops = map(lambda x : x[0],setup_ops)
        self.setup_ops : List[SetupOperationNode] =\
           [ so for so in unwrapped_setup_ops if so is not None ]
    def __str__(self):
        return "\n".join(str(o) for o in self.setup_ops)

class Body(ASTNode):
    def __init__(self, ops : List[Operation]):
        unwrapped_ops = map(lambda x : x[0],ops)
        self.ops : List[Operation] =\
            [ o for o in unwrapped_ops if o is not None ]
    def __str__(self):
        return "\n".join(str(o) for o in self.ops)        

class TDFile(ASTNode):
    def __init__(self, header : Header, body : Body):
        self.header = header
        self.body = body
    def __str__(self):
        return str(self.header)+"\n\n"+str(self.body)

class DJTreeVisitor (NodeVisitor):
    # Note that this is a bottom-up visitor.

    def generic_visit(self, node, visited_children): return visited_children or node

    def visit_comment(self,node,_children): return Comment(node.text)
    def visit__meaningless(self,_node,_children): return None
    def visit_file(self,_node,children): (h, b) = children ; return TDFile(h,b)
    def visit_header(self,_node,children): return Header(children)
    def visit_body(self,_node,children): return Body(children)

    def visit_identifier(self, node, _): return node.text
    def visit_op_operator(self, node, _) : return node.text
    def visit_float_value(self, node, _): return float(node.text)
    def visit_int_value(self, node, _): return int(node.text)
    def visit_python_identifier(self, node, _): return node.text
    def visit_python_value(self, node, _): return node.text
    def visit_quoted_string(self, node, _children):        
        raw_text = node.text
        return unescape(raw_text[1:len(raw_text)-1])


    def visit_ignore(self, node, children):        
        (_ignore,_ws,filename) = children     
        return IgnoreEntries(filename)


    def visit_set(self, node, children):        
        (_set,_ws,name) = children
        return SetDefinition(name)


    def visit_config(self, node, children):        
        (_config,_ws,module_name,_ws,field_name,_ws,value) = children        
        return ConfigureOperations(module_name,field_name,value)


    def visit_def(self, _node, visited_children):
        (_def,_ws,identifier,_ws,op_defs) = visited_children
        return MacroDefinition(identifier,op_defs)


    def visit_op_defs(self,node,visited_children):
        (raw_op_modifier,[op_def],raw_child_op_defs) = visited_children

        if isinstance(op_def, Node):
            raise NotImplementedError(f"visit method missing for {op_def.text}?")

        if isinstance(raw_op_modifier,list):
            op_modifier = raw_op_modifier[0][0].text
            if op_modifier == "+":
                op_def = KeepAlwaysModifier(op_def)
            elif op_modifier == "*":
                op_def = KeepOnlyIfFilteredModifier(op_def)
            elif op_modifier == "!":
                op_def = NegateFilterModifier(op_def)
        
        op_defs = [op_def]
        # lift the subsequent nodes/operations to a list
        if isinstance(raw_child_op_defs,list):
            next_ops = raw_child_op_defs[0][1].ops
            op_defs.extend(next_ops)
        elif isinstance(raw_child_op_defs,Node):
            if len(raw_child_op_defs.children) > 0:
                (_ws,next) = raw_child_op_defs
                op_defs.extend(next.ops)           
        else:
            raise IllegalStateError(f"unexpected value {type(raw_child_op_defs)}: {raw_child_op_defs}")
        
        return ComplexOperation(op_defs)


    def visit_macro_call(self,node,visited_children): 
        (_do,_ws,identifier) = visited_children
        return MacroCall(identifier,...)
    def visit_set_store(self,node,visited_children) : 
        ([store_op],_ws,identifier,_para,_ws,op_defs,_ws,_para) = visited_children
        op = store_op.text
        if  op == "store_in":
            return StoreInSet(identifier,op_defs)        
        elif op == "store_filtered_in":
            return StoreFilteredInSet(identifier,op_defs)        
        else:
            raise ValueError(f"unexpected operation name: {op}")
    def visit_set_use(self,node,visited_children) : 
        (_use,_ws,identifier) = visited_children
        return Use(identifier)
    def visit_or(self,node,visited_children): 
        (_or_ws,cop,more_cops,_ws) = visited_children
        # more_cops is a list or tuples where the second tuple 
        # value is the complex operation
        cops = map(lambda x: x[1], more_cops) # strip "ws" nodes
        all_cops = [cop]
        all_cops.extend(cops)
        return Or(all_cops)

    def visit_report(self,node,_children): return REPORT    
    def visit_write(self,node,children):
        (_write,_ws,filename) = children
        return Write(filename)    

    # IN THE FOLLOWING: 
    #       "n" stands for Node and 
    #       "c" stands for the visited children
    #       "_" is used for things that are not relevant
    def visit_min(self,_n,c): (_,_,op,_,v)=c ; return Min(op,v)
    def visit_max(self,_n,c): (_,_,op,_,v)=c ; return Max(op,v)
    def visit_is_sc(self,_n,_c): return IS_SC
    def visit_is_pattern(self,_n,_c): return IS_PATTERN
    def visit_is_walk(self,_n,_c): return IS_WALK
    def visit_is_regular_word(self,_n,_c): return IS_REGULAR_WORD
    def visit_is_popular_word(self,_n,_c): return IS_POPULAR_WORD
    def visit_sieve(self,_n,c): (_,_,f)=c ; return Sieve(f)
    def visit_get_no(self,_n,_c): return GET_NO
    def visit_get_sc(self,_n,_c): return GET_SC
    def visit_deduplicate_reversed(self,_n,_c): return DEDUPLICATE_REVERSED
    def visit_deduplicate(self,_n,_c): return DEDUPLICATE
    def visit_detriplicate(self,_n,_c): return DETRIPLICATE
    def visit_segments(self,_n,c): (_,_,l)=c ; return Segments(l)
    def visit_strip_ws(self,_n,_c): return STRIP_WS
    def visit_fold_ws(self,_n,_c): return FOLD_WS
    def visit_remove_ws(self,_n,_c): return REMOVE_WS
    def visit_lower(self,_n,_c): return LOWER
    def visit_upper(self,_n,_c): return UPPER
    def visit_capitalize(self,_n,_c): return CAPITALIZE
    def visit_remove_no(self,_n,_c): return REMOVE_NO
    def visit_remove_sc(self,_n,_c): return REMOVE_SC
    def visit_strip_no_and_sc(self,_n,_c): return STRIP_NO_AND_SC
    def visit_reverse(self,_n,_c): return REVERSE
    def visit_replace(self,_n,c): (_,_,f)=c ; return Replace(f)
    def visit_map(self,_n,c): (_,_,s,_,ts)=c ; return Map(s,ts)
    def visit_pos_map(self,_n,c): (_,_,pm)=c ; return PosMap(pm)
    def visit_split(self,_n,c): (_,_,s) = c ; return Split(s)
    def visit_sub_split(self,_n,c): (_,_,s) = c ; return SubSplit(s)
    def visit_number(self,_n,c): (_,_,cs) = c ; return Number(cs)
    def visit_discard_endings(self,_n,c): (_,_,f)=c ; return DiscardEndings(f)
    def visit_mangle_dates(self,_n,_c): return MANGLE_DATES
    def visit_deleetify(self,_n,_c): return DELEETIFY
    def visit_related(self,_n,c): (_,_,r)=c ; return Related(r)    
    def visit_correct_spelling(self,_n,_c): return CORRECT_SPELLING
    
def main():
    parser = argparse.ArgumentParser(
        description=
        """Reads and prints a TD file - primarily useful for debugging purposes."""
    )
    parser.add_argument(
        '-o', 
        '--operations', 
        help="a .td file with the specified operations"
    )
    args = parser.parse_args()
    if args.operations:
        with open(args.operations,mode="r") as f:
            td_file = f.read()
    else:
        #td_file = DJ_SIMPLE_EXAMPLE_FILE
        td_file = DJ_EXAMPLE_FILE

    print("Source:")
    print("=====================================================================")
    tree = DJ_GRAMMAR.parse(td_file)
    
    print("Syntaxtree:")
    print("=====================================================================")    
    print(tree)

    print("AST:")
    print("=====================================================================")    
    ast : TDFile = DJTreeVisitor().visit(tree)
    print(ast)

if __name__ == '__main__':
    sys.exit(main())