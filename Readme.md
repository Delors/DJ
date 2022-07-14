# TransformDictionary

python3 TransformDictionary.py [-r <Rules File>] [-f <Dictionary.utf8.txt>]

Reads from standard-in or the specified file a dictionary and performs the transformations specified in the given rules file. If no rule-file is specified, the default file: `default_rules.td` will be used.


## Rules File

A rules file consists of one or multiple rules where each rule is composed of multiple atomic rules. _The order in which the atomic rules are specified is relevant!_

rule ::= <atomic rule>[WS<atomic rule>]

### Atomic Rules
(See code for now.)