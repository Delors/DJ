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


{ is_pattern write "found_patterns.txt" }!> NO_PATTERN
use NO_PATTERN { is_walk write "found_walk.txt" }!> NO_PATTERN_NO_WALK
use NO_PATTERN_NO_WALK { is_regular_word }!> NON_REGULAR_WORDS { report }> REGULAR_WORDS
use NON_REGULAR_WORDS { is_popular_word }!> REST report
use REST correct_spelling report

#use REGULAR_WORDS related 0.7 report


