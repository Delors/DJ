# GENERAL FILTER
ignore "Ignore.txt"

# DEFINITIONS OF MACROS
def P_UMLAUT_TO_ASCII +replace "UmlautToAscii.txt"
def P_REWRITE_UMLAUT +replace "RewriteUmlaut.txt"
def P_SC_TO_SPACE +replace "SpecialCharToSpace.txt"
# REMARKS
# - "upper" only makes sense for "non-mobile phone" passwords
# - "remove_numbers" potentially leads to many non-sense words.
# - "deleetify" is a computationally intensive operation and the results
#             of it may depend on the time when the deleetification
#             is performed.
# - "number" may lead to many new entries, use sparingly!
def BASE_TRANSFORMATIONS P_SC_TO_SPACE +map \s [._-] +strip_ws +deleetify +capitalize +remove_sc +get_numbers +get_sc +lower P_UMLAUT_TO_ASCII P_REWRITE_UMLAUT +remove_ws +number [aeiou]

# RULES
# A rule takes an entry and generates new candidates.
# In general, entries to which a rule does not apply, basically which
# remain as is, are filtered. However, this behavior can be modified:
# A "+" directly in front of the rule will
# ensure that the original entry is passed on to the next step.
# " A "*" directly in front of the rule will ensure that the 
# entry is passed on if and only if it was not transformed. 

BASE_TRANSFORMATIONS report
split / BASE_TRANSFORMATIONS report
split . BASE_TRANSFORMATIONS report
mangle_dates report
split \s discard_endings "discard_endings.txt" BASE_TRANSFORMATIONS report




