ignore "ignore/de.txt"
ignore "ignore/en.txt"
ignore "ignore/fr.txt"


set NO_PATTERN
set NO_PATTERN_NO_WALK
set REGULAR_WORDS
set NON_REGULAR_WORDS
set REST

def BASE_TRANSFORMATIONS \
 +strip_no_and_sc \
 !is_pattern \
 !is_walk \
 *replace "replace/SpecialCharToSpace.txt" \
 *strip_ws \
 *fold_ws \
 *split "\s" \
 *deduplicate \
 *deduplicate_reversed \
 *detriplicate \
 min length 3 \
 *deleetify \
 +capitalize 

#store in PATTERN: is_pattern write "found_patterns.txt"
#is_walk write "found_keyboard_walks.txt"

#do BASE_TRANSFORMATIONS is_popular_word related 0.6
#do BASE_TRANSFORMATIONS is_regular_word related 0.5
#do BASE_TRANSFORMATIONS !is_popular_word !is_regular_word correct_spelling report related 0.8

{ is_pattern write "found_patterns.txt" }!> NO_PATTERN
use NO_PATTERN { is_walk write "found_walk.txt" }!> NO_PATTERN_NO_WALK
use NO_PATTERN_NO_WALK { is_regular_word }!> NON_REGULAR_WORDS { report }> REGULAR_WORDS
use NON_REGULAR_WORDS { is_popular_word }!> REST report
use REST correct_spelling report

#use REGULAR_WORDS related 0.7 report


