from parsimonious.grammar import Grammar

grammar_complete = Grammar(
    r"""
    file            = header stmt+
    header          = ( ( def / ignore / set / config / comment / empty_line ) eol )*
    stmt            = ( ( op_defs / comment / empty_line ) eol )*
    comment         = ~r"#[^\r\n]*" nl 
    empty_line      = inline_ws* nl
    nl              = ~r"[\r\n]+"
    eol             = inline_ws* nl

    def             = "def" inline_ws+ identifier inline_ws+ op_defs
    ignore          = "ignore" inline_ws+ file_name
    set             = "set" inline_ws+ identifier
    config          = "config" inline_ws+ python_identifier inline_ws+ python_identifier inline_ws+ python_value
                             
    op_defs         = op_def (inline_ws+ op_def)* 
    op_def          = op_modifier? op
    op_modifier     = "+" / "*" / "!"

    op              = report / 
                      related / 
                      min_length / 
                      strip_ws

    report          = "report"
    strip_ws        = "strip_ws"
    related         = "related" inline_ws+ float_value    
    min_length      = "min_length" inline_ws+ int_value 

    
    file_name       = quoted_string
    quoted_string   = ~'"[^"]+"'
    float_value     = ~r"[0-9]+(\.[0-9]+)?"
    int_value       = ~r"[1-9][0-9]*"
    python_identifier = ~r"[a-zA-Z_]+"
    python_value    = ~r"[a-zA-Z0-9._]+"
    identifier      = ~r"[A-Z]+"    
    inline_ws       = ~r"[ \t]"
    """
)

grammar = Grammar(
    r"""    
    file            = header body 
    header          = ( ignore / set / config / def / comment / _meaningless ) *
    body            = ( op_defs / comment / _meaningless ) +
    
    nl              = ~r"[\r\n]"m
    ws              = ~r"[ \t]"
    _meaningless    = ws* nl?
    comment         = ~r"#[^\r\n]*"    
    quoted_string   = ~'"[^"]*"'
    file_name       = quoted_string
    identifier      = ~r"[A-Z]+"a
    float_value     = ~r"[0-9]+(\.[0-9]+)?"
    int_value       = ~r"[1-9][0-9]*"
    python_identifier = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
    python_value    = ~r"[a-zA-Z0-9._]+"

    ignore          = "ignore" ws+ file_name
    set             = "set" ws+ identifier
    config          = "config" ws+ python_identifier ws+ python_identifier ws+ python_value
    def             = "def" ws+ identifier ws+ op_defs

    op_defs         = op_def (ws+ op_def)* 
    
    op_def          = report /
                      min_length /
                      related /
                      strip_ws
    
    report          = "report"
    min_length      = "min_length" ws+ int_value 
    strip_ws        = "strip_ws"
    related         = "related" ws+ float_value    
    
    """
)

example_0 = """#Comment"""
example_0_nl = """#Comment
"""

example_1 = """report"""
example_1_nl = """report
"""
example_1_nl_nl = """
report
"""

example_1_1_11_nl_nl = """
report
report
report report
"""

example_2 = """
#Comment

ignore "abc/def.txt"

set PATTERNS

config related KEEP_ALL_RELATEDNESS 0.75

def SIMPLE related 0.5 report min_length 3

strip_ws min_length 3 report

related 0.5 report report"""

example_3 = """
# GENERAL FILTER
ignore "ignore/de.txt"

set PATTERNS

config related K 15
config related KEEP_ALL_RELATEDNESS 0.75

def SIMPLE related 0.5 report min_length 3

#min_length 3 
report

"""

tree = grammar.parse(example_2)
print(tree)
