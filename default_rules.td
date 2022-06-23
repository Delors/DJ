# GENERAL FILTER
ignore "Ignore.txt"

# DEFINITIONS OF CUSTOM RULES
def UMLAUT_TO_ASCII replace "UmlautToAscii.txt"
def REWRITE_UMLAUT replace "RewriteUmlaut.txt"
def SC_TO_SPACE replace "SpecialCharToSpace.txt"
# REMARKS
# - Adding "+to_upper" only makes sense for "non-mobile phone" passwords
# - Adding "+remove_numbers" potentially leads to many non-sense words.
# - "deleetify" is a computationally intensive operation and the results
#             of it may depend on the time when the deleetification
#             is performed ()
def BASE_TRANSFORMATIONS +SC_TO_SPACE +strip +deleetify +capitalize +remove_sc +get_numbers +get_sc +to_lower +UMLAUT_TO_ASCII +REWRITE_UMLAUT +remove_ws

# RULES
# A "+" directly in front of the rule will
# ensure that the original entry is passed on to the next step.
# " A "*" directly in front of the rule will ensure that the 
# entry is passed on if and only if it was not transformed. 
# In general, entries which are unchanged by a transformer
# are filtered.
BASE_TRANSFORMATIONS report
split / BASE_TRANSFORMATIONS report
split . BASE_TRANSFORMATIONS report
split \s *discard_endings "discard_endings.txt" BASE_TRANSFORMATIONS report


