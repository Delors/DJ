# GENERAL FILTER
ignore "Ignore.txt"

def BASE_TRANSFORMATIONS 
\ *strip_numbers_and_sc
\ !is_pattern
\ *replace "SpecialCharToSpace.txt"
\ *strip_ws 
\ *fold_ws 
\ *split \s 
\ +deduplicate
\ min_length 3 
\ *deleetify

related



