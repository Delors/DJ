from parsimonious.grammar import Grammar

"""
Grammar of TD files. 

Please note, PEGs do greedy matching and that, e.g., "deduplicate_reversed" 
has to be defined in the or group before "deduplicate" otherwise
"dedpulicate" would match the first part of a "deduplicate_reversed" op
and the "_reversed" would remain unmatched.
"""
DJ_GRAMMAR = Grammar(
    r"""    
    file            = header body 
    header          = ( ignore / set / config / def / comment / _meaningless ) *
    body            = ( op_defs / comment / _meaningless ) +
    
    nl              = ~r"[\r\n]"m
    ws              = ~r"[ \t]"
    _meaningless    = ws* nl?
    continuation    = ( ws+ ~r"\\[\r\n][ \t]+"m ) / ws+
    comment         = ~r"#[^\r\n]*"    
    quoted_string   = ~'"[^"]*"'
    file_name       = quoted_string
    identifier      = ~r"[A-Z_]+"a
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
                      not /
                      or /
                      report /
                      write /
                      min_length /                      
                      strip_ws /
                      fold_ws /
                      strip_numbers_and_sc /                      
                      deduplicate_reversed /
                      deduplicate /                      
                      detriplicate /
                      deleetify /
                      capitalize /
                      replace /
                      split /
                      is_pattern /
                      is_walk /
                      is_regular_word /
                      is_popular_word /
                      correct_spelling /
                      related 
                      
    macro_call      = "do" ws+ identifier

    # Handling of (intermediate) sets
    #
    set_store       = "store_in" ws+ identifier "(" ws* op_defs ws* ")"
    # a set use always has to be the first op in an op_defs
    set_use         = "use" ws+ identifier

    # Meta operators that can only be combined with filters
    #
    not             = ~r"not\(\s*" op_defs ~r"\s*\)"
    #or              = "or(" ws* op_defs (ws* "," ws* op_defs)+ ws* ")"
    or              = ~r"or\(\s*" op_defs ( ~r"\s*,\s*" op_defs )+ ~r"\s*\)"

    # Built-in operators
    #
    report          = "report"
    write           = "write" ws+ file_name

    # Modularied operators
    #
    min_length      = "min_length" ws+ int_value 
    
    strip_ws        = "strip_ws"
    fold_ws         = "fold_ws"
    strip_numbers_and_sc = "strip_numbers_and_sc"
    deduplicate_reversed = "deduplicate_reversed"
    deduplicate     = "deduplicate"    
    detriplicate    = "detriplicate"
    deleetify       = "deleetify"

    capitalize      = "capitalize"

    replace         = "replace" ws+ file_name
    split           = "split" ws+ quoted_string

    is_pattern      = "is_pattern"
    is_walk         = "is_walk"
    is_regular_word = "is_regular_word"
    is_popular_word = "is_popular_word"

    correct_spelling = "correct_spelling"
    related         = "related" ws+ float_value    
    
    """
)

example_demo = """
# This is just a demo!!!
ignore "ignore/de.txt"

config related K 15
config related KEEP_ALL_RELATEDNESS 0.75

set NO_PATTERN
set WALK
set RELATED
set NO_WORD

def BASE_TRANSFORMATIONS \
 *strip_numbers_and_sc \
 !is_pattern \
 *replace "replace/SpecialCharToSpace.txt" \
 *split "\s" \
 *strip_ws \
 *fold_ws \
 +deduplicate \
 min_length 3 \
 *deleetify

+related 0.5 min_length 3 
do BASE_TRANSFORMATIONS 

store_in WALKS(is_walk)
store_in NO_PATTERNS( not( is_pattern ) )

store_in NO_WORD(or(is_walk,is_pattern))

store_in RELATED( *split "\s" \
 *strip_ws \
 *fold_ws \
 related 0.5 )

use NO_PATTERNS
"""


tree = DJ_GRAMMAR.parse(example_demo)
print(tree)
