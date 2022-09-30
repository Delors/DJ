# GENERAL FILTER
ignore "Ignore.txt"

def BASE_TRANSFORMATIONS 
\ *strip_numbers_and_sc
\ (NO_PATTERN)!<!is_pattern
\ *replace "SpecialCharToSpace.txt"
\ *strip_ws 
\ *fold_ws 
\ *split \s 
\ +deduplicate
\ min_length 3 
\ *deleetify

BASE_TRANSFORMATIONS is_popular_word
#BASE_TRANSFORMATIONS is_regular_word
#BASE_TRANSFORMATIONS !is_popular_word !is_regular_word correct_spelling





