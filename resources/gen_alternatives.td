# Generators are used to generate new dictionary entries.
# The generated words are created and processed before the entries of a 
# dictionary. However, to the rest of the operations it makes not difference
# if the entries are read from a file or are generated.
#
# This kind of generators is particular usefull if some characters
# should be replaced by related characters.

gen alt [["T","t"],["es"],["T","t"]]
gen alt [["F","f"],["E","e","3","é","è",""],["st","St","sT"]]

# let's filter some of the generated entries
max upper 1 report
