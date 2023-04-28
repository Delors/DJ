ignore "ignore/de.txt"
ignore "ignore/en.txt"
ignore "ignore/fr.txt"


set STRIPPED_MINIMIZED
set NO_SEQUENCE
set NO_PATTERN
set NO_SEQ_NO_PATTERN_NO_WALK
set NO_WORD
set UNKNOWN_1
set UNKNOWN_2
set CROPPED
set GARBAGE

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
    { is_walk }!> NO_SEQ_NO_PATTERN_NO_WALK                 write "walks.txt"

use NO_SEQ_NO_PATTERN_NO_WALK \
    { do IS_WORD }!> NO_WORD                                write "simple_words.txt"

use NO_WORD \
    do ADVANCED_TRANSFORMATIONS \
    min length 4 \
    { +find_all "[A-Z][a-z]*" \
      do IS_WORD }!> UNKNOWN_1                              write "no_simple_words.txt"

# ATTENTION: using "correct_spelling" may lead to many new words which
#            is undesirable if we just want to find "original" words!  
# use NO_WORD { correct_spelling *strip_no_and_sc }/> UNKNOWN write "words.txt"  

# When we reach this point, the initial entry was no direct pattern,
# no (keyboard)walk, no regular word and also no popular word; 
use UNKNOWN_1 { cut l 1 2 }> CROPPED
use UNKNOWN_1 { cut r 1 2 }> CROPPED
use UNKNOWN_1 { cut l 1 1 cut r 1 1 }> CROPPED                 

use CROPPED \
    do ADVANCED_TRANSFORMATIONS \
    min length 4 \
    {   +find_all "[A-Z][a-z]*" \
        do IS_WORD }!> UNKNOWN_2 \ 
    min length 4                                           write "cropped_words.txt"


# Now, let's do some splitting up of the entry to find subwords; 
# we no longer check for typos or something similar, because from
# our experience passwords made up out of multiple words contain
# no significant typos.

use UNKNOWN_2 { find_all "[A-Z][a-z]*" }!> GARBAGE         write "sub_words.txt"

use GARBAGE                                                write "garbage.txt"

