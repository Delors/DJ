# GENERAL FILTER
ignore "Ignore.txt"


#set PATTERNS Entries wich were patterns.
# \ >PATTERN
# \ !>NO_PATTERN
# use PATTERN

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

store in PATTERN: is_pattern write "found_patterns.txt"
is_walk write "found_keyboard_walks.txt"

do BASE_TRANSFORMATIONS is_popular_word related 0.6
do BASE_TRANSFORMATIONS is_regular_word related 0.5
do BASE_TRANSFORMATIONS !is_popular_word !is_regular_word correct_spelling report related 0.8





