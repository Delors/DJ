# GENERAL FILTER
# Applies basic transformations to a real world dictionary to
# generate password like entries.

ignore "Ignore.txt"

# DEFINITIONS OF MACROS
def UMLAUT_TO_ASCII replace "UmlautToAscii.txt"
def REWRITE_UMLAUT replace "RewriteUmlaut.txt"
def SC_TO_SPACE replace "SpecialCharToSpace.txt"
# REMARKS
# - "upper" only makes sense for "non-mobile phone" passwords
# - "remove_numbers" potentially leads to many non-sense words.
# - "deleetify" is a computationally intensive operation and the results
#             of it may depend on the time when the deleetification
#             is performed.
# - "number" may lead to many new entries, use sparingly!
def BASE_TRANSFORMATIONS +SC_TO_SPACE +strip +deleetify +capitalize +remove_sc +get_numbers +get_sc +lower +UMLAUT_TO_ASCII +REWRITE_UMLAUT +remove_ws +number [aeiou]

# RULES
# A rule takes an entry and generates new candidates.
# In general, entries which are unchanged by a transformer
# are filtered.
# A "+" directly in front of the rule will
# ensure that the original entry is passed on to the next step.
# " A "*" directly in front of the rule will ensure that the 
# entry is passed on if and only if it was not transformed. 

BASE_TRANSFORMATIONS report
split / BASE_TRANSFORMATIONS report
# split . BASE_TRANSFORMATIONS report
mangle_dates report
split \s discard_endings "discard_endings.txt" BASE_TRANSFORMATIONS report




