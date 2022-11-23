# GENERAL FILTER
ignore "Ignore.txt"


#set PATTERNS Entries wich were patterns.
# \ PATTERNS<!is_pattern

def BASE_TRANSFORMATIONS 
\ +strip_numbers_and_sc
\ !is_pattern
\ !is_keyboard_walk
\ *replace "SpecialCharToSpace.txt"
\ *strip_ws 
\ *fold_ws 
\ *split \s 
\ *deduplicate
\ *deduplicate_reversed
\ *detriplicate
\ min_length 3 
\ *deleetify
\ +capitalize

is_pattern write "found_patterns.txt"
is_walk write "found_keyboard_walks.txt"

BASE_TRANSFORMATIONS is_popular_word related 0.6
BASE_TRANSFORMATIONS is_regular_word related 0.5
BASE_TRANSFORMATIONS !is_popular_word !is_regular_word correct_spelling report related 0.8





