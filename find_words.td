# GENERAL FILTER
ignore "Ignore.txt"

# \ (NO_PATTERN<!)!is_pattern
def BASE_TRANSFORMATIONS 
\ *strip_numbers_and_sc
\ !is_pattern
\ *replace "SpecialCharToSpace.txt"
\ *strip_ws 
\ *fold_ws 
\ *split \s 
\ *deduplicate
\ *detriplicate
\ min_length 3 
\ *deleetify

BASE_TRANSFORMATIONS report
#BASE_TRANSFORMATIONS is_popular_word
#BASE_TRANSFORMATIONS is_regular_word
#BASE_TRANSFORMATIONS !is_popular_word !is_regular_word correct_spelling





