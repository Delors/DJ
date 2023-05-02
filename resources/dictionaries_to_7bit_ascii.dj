# Applies basic transformations to a real world dictionary to
# generate base words for passwords.

# We want to handle, e.g., the following situations:

# Input: 
#   Frankfurt an der Oder
# Output:  
#   FrankfurtanderOder
#   Frankfurt
#   Oder
#
# Input:
#   Achkhoj-Martanovskij Rajon
# Output:
#   Achkhoj-Martanovskij
#   AchkhojMartanovskij
#   Achkhoj
#   Martanovskij
#   Rajon

set NON_7BIT_ASCII

# GENERAL FILTER

ignore "ignore/de.txt"
ignore "ignore/en.txt"
ignore "ignore/es.txt"
ignore "ignore/fr.txt"
ignore "ignore/al.txt"



# DEFINITIONS OF MACROS
def LETTERS_TO_ASCII \
    *replace "resources/replace/AsortedLettersToAscii.txt" \
    *replace "resources/replace/CroatianLettersToAscii.txt" \
    *replace "resources/replace/DanishLettersToAscii.txt" \
    *replace "resources/replace/FrenchLettersToAscii.txt" \
    *replace "resources/replace/LithuanianLettersToAscii.txt" \
    *replace "resources/replace/PolishLettersToAscii.txt" \
    *replace "resources/replace/SpanishLettersToAscii.txt" \
    *replace "resources/replace/SpecialCharToSpace.txt" \
    *replace "resources/replace/TurkishLettersToAscii.txt" \
    +replace "resources/replace/RewriteUmlaut.txt" \
    *replace "resources/replace/UmlautToAscii.txt" 

def SC_TO_SPACE *replace "replace/SpecialCharToSpace.txt"

*strip "`'’" \
    do LETTERS_TO_ASCII \
    +split " " \
    +remove_sc \
    *remove_ws \
    +capitalize \
    { sieve "sieve/7bit-ASCII.txt" }!> NON_7BIT_ASCII \
    min length 3 \
    report

# If you need to check that only expected values are filtered!
# use NON_7BIT_ASCII write "non-7bit-ASCII.txt"



