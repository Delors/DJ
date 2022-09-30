# Dictionary Transformation and Generation aka `Dictionary Juggling` (DJ)

Processes the entries of a dictionary by applying one to multiple user-definable transformations, extractions and/or filtering operations. 
Basically, DJ enables the trivial definition of user-defineable transformation 
pipelines.

## Installation

To execute basic operations (e.g. `strip`,`remove`,`fold`,..), no special installation steps/downloads are necessary. However, to use the advanced "semantic-based" features, several dictionaries and pre-trained NLP models are required. Some will be downloaded automatically and some need to be pre-installed.

### 1. Download dictionaries
Some of the available operations need well defined dictionaries as a foundation. 
These dictionaries need to be the `hunspell` dictionaries used by [libreoffice](https://github.com/LibreOffice/dictionaries) and need to be placed in the folder `dicts`.

```sh
mkdir dicts
cd dicts
git clone --depth 1 https://github.com/LibreOffice/dictionaries
cd ..
```

### 2. Install necessary libraries  
```sh
pip3 install -r requirements.txt
```

## Usage

Reads in a (case) specific dictionary and generates an output dictionary by processing each input entry according to some well defined operations. Additionally, this tool can also be used to analyze existing dictionaries.

```sh
python3 TransformDictionary.py [-o <Operations File>] [-d <Dictionary.utf8.txt>]
```

Reads from standard-in or the specified file (`-d`) a dictionary and performs the operations specified in the given operations file. If no operations-file is specified, the default file: `default_ops.td` will be used, which - however - primarily serves demonstration purposes.

## Operations File

An operations file (`td`) consists of one or multiple (complex) operations which are performed for each entry. Each complex operation is composed of multiple atomic operations where the order in which the atomic operations are specified is generally relevant.

In general the syntax is simply:
```
operation ::= <atomic operation>[WS<atomic operation>]
```

### Basic example

An operations file in its simplest case just contains a single operation, e.g.:

```sh
# Example 1
remove_ws
```

In this case the white space of each entry will be removed and the transformed entry/entries will be passed on to the next operation. Entries which have no white space will not be passed on. If entries which have no white space should be passed on to the next operation, two operation modifiers exist:
 
 1. the '+' operator (e.g. '+remove_ws') which will always pass on the original entry to the next operation.
 2. the '*' operator (e.g. '*remove_ws') which will pass on the original entry iff a transformation/an extraction didn't apply; i.e., the operation made no changes/didn't find anything relevant. However, if an effective transformation is performed, the original entry is no longer passed on to the next operation.

To print out the current state of an entry, the `report` operation is used. However, a report operation is automatically added at the end of an operations definition. Therefore, the example from above is equivalent to:

```sh
remove_ws report
```

### Chaining operations example

Let's assume that you have entries such as `Audi RS` in your dictionary and you want to generate the following passwords:

```txt
Audi-RS
Audi_RS
audi-rs
audi_rs
AudiRS
audirs
Audi
audi
RS
rs
```

In this case you have to chain multiple operations to get the desired output:

```sh
# Example 2
+split \s +remove_ws *map \s [-_] +lower report
```

The first operation (`+split \s`) will split up entries using a whitespace as the split character (`\s`). Additionally the original entry is always passed on (`+`). For example, in this case the two new entries `Audi` and `RS` are generated. The second operation will remove the whitespace from the original entry and simple keep the others. After that, we will map each whitespace to either "-" or "_" (`*map \s "-_"`); the `*` operator is used to ensure that entries with a space will no longer be passed on. Effectively, the original "Audi RS" is filtered. The `+lower` operation will then additionally create lower case representations of all current (intermediate) results. At last, we simply print out all results.

As said, the order of operation definitions is relevant and if the order would have been:

```sh
# Example 3
*map \s [-_] +split \s +remove_ws +lower report
```
the output of the transformation would "just" be:

```txt
audi-rs
Audi-RS
audi_rs
Audi_RS
``` 

To foster readability of long operation definitions it is possible to split up an operations definition over multiple lines by starting the next lines using "\ " at the beginning of a line. This is then treated as a continuation of the previous line.  Hence, the above rule (Example 2) can also be written as:

``` 
+split \s 
\ +remove_ws 
\ *map \s [-_]
\ +lower report
```

## Atomic Operations
(See code for now.)