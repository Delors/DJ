from parsimonious.grammar import Grammar


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

    op_defs         = op_modifier? op_def (ws+ op_def)* 

    op_modifier     = "+" / "*" / "!"
    
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

example_2 = """
#Comment

ignore "abc/def.txt"

set PATTERNS

config related KEEP_ALL_RELATEDNESS 0.75

def SIMPLE related 0.5 report min_length 3

*strip_ws min_length 3 report

related 0.5 report report"""

tree = grammar.parse(example_2)
print(tree)
