# GENERAL FILTER
ignore "Ignore.txt"

config Related K 15
config Related KEEP_ALL_RELATEDNESS 0.75

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


+related 0.5 min_length 3 


