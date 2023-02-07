# This script demonstrates how to find words related to the words of a dictionary.
#
# This script assumes that the words are already real world words found on 
# webpages such as Facebook, Twitter etc..
# In other words, this script assumes that the respective preprocessing has already occured.

# GENERAL FILTER
ignore "ignore/de.txt"

# The following parameters basically control the number of related words
# that we want 
config related K 20
config related KEEP_ALL_RELATEDNESS 0.75

# We will search for related words in a multistep process.
set STEP_ONE
set STEP_TWO

{ related 0.5 }> STEP_ONE               write "most_related.txt"
use STEP_ONE { related 0.6 }> STEP_TWO  write "related.txt"
use STEP_TWO related 0.7                write "least_related.txt"

