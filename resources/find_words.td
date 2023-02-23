ignore "ignore/de.txt"
ignore "ignore/en.txt"
ignore "ignore/fr.txt"


set STRIPPED_MINIMIZED
set NO_SEQUENCE
set NO_PATTERN
set NO_PATTERN_NO_WALK
set NO_WORD
set UNKNOWN
set CUT_BASE

def IS_WORD \
 or( is_regular_word, is_popular_word )

def BASE_TRANSFORMATIONS \
 *strip_no_and_sc \
 *replace "replace/SpecialCharToSpace.txt" \
 *strip_ws \
 *fold_ws \
 *split  " "

def ADVANCED_TRANSFORMATIONS \
 *deduplicate \
 *deduplicate_reversed \
 *detriplicate \
 +reverse \
 *deleetify \
 +capitalize 

# Split up the dictionary in multiple parts

{ do BASE_TRANSFORMATIONS }> STRIPPED_MINIMIZED

use STRIPPED_MINIMIZED \
    { or( 
        is_part_of "abcdefghijklmnopqrstuvwxyz",
        is_part_of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        ) \
    }!> NO_SEQUENCE                                         write "sequences.txt" 

use NO_SEQUENCE \
    { is_pattern }!> NO_PATTERN                             write "patterns.txt"

use NO_PATTERN \
    { is_walk }!> NO_PATTERN_NO_WALK                        write "walks.txt"

use NO_PATTERN_NO_WALK \
    { do IS_WORD }!> NO_WORD                                write "words.txt"
    
use NO_WORD { correct_spelling *strip_no_and_sc }/> UNKNOWN write "words.txt"  

# When we reach this point, the initial entry was no direct pattern,
# no (keyboard)walk, no regular word and also no popular word; 
# additionally, simple corrections where also not successfull;
# hence a simple "cut l 1 1" or "cut r 1 1" is useless.
use UNKNOWN { cut l 2 2 do ADVANCED_TRANSFORMATIONS }> CUT_BASE
use UNKNOWN { cut r 2 2 do ADVANCED_TRANSFORMATIONS }> CUT_BASE
use UNKNOWN { cut l 1 1 cut r 1 1 do ADVANCED_TRANSFORMATIONS }> CUT_BASE                 

use CUT_BASE do IS_WORD                                     write "words.txt"


# Now, let's do some splitting up of the entry to find subwords; 
# we no longer check for typos or something similar, because from
# our experience passwords made up out of multiple words contain
# no significant typos.

# TODO

