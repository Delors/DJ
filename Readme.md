# Dictionary Transformation and Generation for Password Recovery aka `Dictionary Juggling` (DJ)

Processes the entries of a _base_ dictionary by applying one to multiple user-definable transformations, extractions,  filtering or generating operations. 
Basically, DJ enables the trivial definition of user-definable analysis and transformation pipelines to generate dictionaries useable for password recovery.

## Installation

To execute most basic operations (e.g. `strip`, `remove`, `fold`, etc.) no special installation steps/downloads are necessary. However, to use the advanced dictionary and/or NLP-based features, several dictionaries and pre-trained NLP models are required. Some will be downloaded automatically and some need to be pre-installed. I.e., on first usage of the respective features DJ needs an Internet connection. Alternatively, the respective packages can be downloaded externally and then be installed for complete offline usage.

### 1. Download dictionaries
Some of the available operations need well defined dictionaries as a foundation. 
These dictionaries need to be `hunspell` dictionaries. DJ relies on those used by [libreoffice](https://github.com/LibreOffice/dictionaries) and the dictionaries need to be placed in the folder `dicts`.

```sh
mkdir dicts
cd dicts
git clone --depth 1 https://github.com/LibreOffice/dictionaries
cd ..
```

### 2. Install necessary libraries  
First, make sure that `nuspell` is installed. E.g., `sudo apt install nuspell`.

Second, install the python libraries.
```sh
pip3 install -r requirements.txt
```

#### Potential Installation Issues

__Gensim and Numpy__  
If you install Gensim using pip and Numpy was already installed using "apt" (i.e., using the system's package manager), errors may appear when you want to use respective operations (e.g., `related` or `is_popular_word`). In this case, _first_ remove the global Numpy installation (e.g., `sudo apt remove python3-numpy`) 

__Pynuspell and Python >3.10__

The `pynuspell` module is not (as of Oct. 2022) available for Python 3.10 and above in the PIP repository. In this case, it must be installed from source if operations (e.g., `correct_spelling` or `is_regular_word`) that use dictionaries are going to be used. 

To install pynuspell from source, you first have to install `nuspell` _and_ also the development package `libnuspell-dev`. After that, head over to [https://pypi.org/project/pynuspell/](https://pypi.org/project/pynuspell/)
and follow the installation instructions; however, be aware that the instructions are not correct for Linux. For Linux (Debian/Ubuntu) you need to do the following:

```bash
sudo apt install cmake
sudo apt install ninja-build
sudo apt-get install pkg-config
git clone --recurse-submodules https://github.com/scherzocrk/pynuspell.git
cd pynuspell
./extern/vcpkg/bootstrap-vcpkg.sh
export VCPKG_ROOT=./extern/vcpkg
./extern/vcpkg/vcpkg install
pip3 install .
```

### 3. Prepare for offline Usage
In general, DJ can be used offline. However, some operations (in particular `related`) require data that will be loaded on demand and will then be stored in the user's home folder. If DJ is to be used on an offline computer this data/the folder then needs to be copied to the offline machine. 

To force DJ to download the necessary data just start DJ with the `related` operation and type a single word:

```bash
$ ./dj.py -v 'is_popular_word related 0.5 report'
Wiesbaden
``` 

This will force the on-demand download of the respective NLP models. Therefore, the first usage may take quite some time as several GB need to be downloaded from the web, loaded 

## Usage

Reads in a (case) specific dictionary and generates an output dictionary by processing each input entry according to some well defined operations. Additionally, DJ can also be used to _just_ analyze existing dictionaries to filter entries.

### Basic Usage

```sh
python3 dj.py <operations>
```

In this case, a dictionary will be read from stdin and then the specified operations will be performed for each entry. 

For example, in case of `python3 DJ.py lower report` every entry of the given dictionary will be converted to lower case and will then be output. Entries which are already in lower case will be ignored. 

_Do not forget to specify `report` or `write "<FILE>"`  at the end; otherwise you'll have no output!_

More complex operations specifications are also possible on the command line using appropriate escaping/parameter expansion. The next example shows how to specify some configuration operations:

```sh
python3 dj.py "config related K 100"$'\n'"related 0.5 related 0.6 related 0.7 report"
```

### Standard Usage

```sh
python3 dj.py [-o <Operations File>] [-d <Dictionary.utf8.txt>]
```

Reads a dictionary from standard-in or the specified file (`-d`)  and performs the operations specified in the given operations file. You can find some template '.dj' files in the resources folder that are related to specific use cases and demonstrate how to use DJ.

## Operations File

An operations file (`dj`) consists of one or multiple (complex) operations which are performed for each entry. Each complex operation is composed of multiple atomic operations where the order, in which the atomic operations are specified, is generally relevant.

In general the syntax is simply:
```
operation ::= <atomic operation>[WS<atomic operation>]
```

### Basic example

An operations file in its simplest case just contains a basic operation and an output operation (`report` or ` write`), e.g.:

```sh
# Example 1
remove_ws report
```

In this case the white space of each entry will be removed and the transformed entry/entries will be passed on to the next operation (`report`). Entries which have no white space will not be passed on. If entries which have no white space should be passed on to the next operation, two operation modifiers exist:
 
 1. the '+' operator (e.g. '+remove_ws') which will always pass on the original entry to the next operation.
 2. the '*' operator (e.g. '*remove_ws') which will pass on the original entry iff a transformation/an extraction didn't apply; i.e., the operation made no changes/didn't find anything relevant. However, if an effective transformation is performed, the original entry is no longer passed on to the next operation. Hence, in case of ` *remove_ws` the entry `Test` will be passed on as is. The entry `Test Test` will
 be transformed to `TestTest` and then passed to the next operation. The original
 `Test Test` will be dropped.

To print out the current state of an entry, the `report` operation is used. 

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
+split " " +remove_ws *map " " "-_" +lower report
```

The first operation (`+split " "`) will split up entries using a whitespace as the split character (`" "`). Additionally, the original entry is always passed on (`+`). For example, in this case the two new entries `Audi` and `RS` are generated. The second operation will remove the whitespace from the original entry and simply keeps the others. After that, we will map each whitespace to either "-" or "_" (`*map " " "-_"`); the `*` operator is used to ensure that entries with a space will no longer be passed on. Effectively, the original "Audi RS" is filtered. The `+lower` operation will then additionally create lower case representations of all current (intermediate) results. At last, we simply print out all results.

As said, the order of operation definitions is relevant and if the order would have been:

```sh
# Example 3
*map " " "-_" +split " " +remove_ws +lower report
```
the output of the transformation would "just" be:

```txt
audi-rs
Audi-RS
audi_rs
Audi_RS
``` 

I.e., in this example the second `+split " "` operation is effectively useless because all spaces were already replaced beforehand.

### Formatting long operation definitions

To foster readability of long chains of operation definitions it is possible to split up a chain of operation definitions over multiple lines by ending a line using "\" (please note, that the "\" has to be the very last character!). This will then be treated as a continuation of the previous line.  Hence, the above rule (Example 2) can also be written as:

```sh 
+split " " \
 +remove_ws \
 *map " " "-_" \
 +lower report
```

## Atomic Operations
Each atomic operation (e.g., `lower`, `min length`, `related`, `get_no`) performs one well-defined transformation, extraction or filtering operation and most operations provide some level of configurability. In general, an operation that does not apply to a certain entry, swallows the entry and does not pass it on to the next operation. This behavior can be modified using the "+" and "*" modifiers as described above.

### Built-in Operations
Additionally, DJ has some built-in directives for special purposes: 
 - `gen <GENERATOR> <python_value>` triggers the specified generator to generate new terms using the specified configuration value.
 - `_` is the nop operation which does nothing and just passes on the entries from the first operation to the next operation. 
 - `def <NAME> <operations>` defines a macro; a defined macro is used using `do <NAME>`. Note that the name of the macro has to use capital letters.
 - `config <operation> <PARAMETER> <python_value>` to configure an operation's global parameters
 - `ignore "<file>"` to specify files with terms that will always be ignored; for example, when processing a dictionary that contains names of locations (e.g., "Frankfurt an der Oder" or "Rotenburg ob der Tauber" or "South Beach" you often want to ignore specific words to avoid cluttering of the generated dictionary. In this case, , "an", "ob", "der", or "South" and maybe even "Beach" are potentially candidates you want to ignore.)

Controlling the output:  
 - `report` to write the result of an operation (sequence) to stdout. 
 - `write "<file>"` to write out the results of a transformation to a specific file instead of `stdout`. Multiple `write` operations can be used and write to the same file.

Using intermediate *sets*:  
It is also possible to capture the (intermediate) result of an operation for later usage. For example, in some cases an intermediate result should be processed in multiple specific manners that are not compatible with each other and the previous operations were computationally expensive (e.g., when using some of the semantics features) or the result should just be given some name. In this case, the result can be stored in an intermediate set and used later on. To use a set, it first needs to be declared using `set <SET_NAME>`. Afterwards, the results of some operations are stored in the set using the set syntax `{ <operation(s)> }> <SET_NAME>`. Alternatively, to store filtered entries `{ <operation(s)> }[]> <SET_NAME>` can be used. The set is used later on by starting an operations chain using `use <SET_NAME>`.

```sh
set STEP_ONE
set STEP_TWO

{ related 0.5 }> STEP_ONE               write "most_related.txt"
use STEP_ONE related 0.6                write "related.txt"
```

(For the documentation of specific operations see the code for now.)

## Development/Debugging of Operations

A design principle of DJ is to make it possible to develop and test operations independently. For example, to test the **related** operation it is trivially possible to use a python console to instantiate the class and to then call the **related** operation as shown in the next example:

```python
/DJ% python3
In [1]: from dj_ast import TDUnit, Header, Body, ComplexOperation
In [2]: from operations.related import Related
In [3]: R = Related()
In [4]: ast = TDUnit(Header([]),Body([ComplexOperation([R])]))
In [5]: ast.init(ast,None)
In [6]: R.process("barca")
[info] loading twitter (this will take time)
[info] loaded twitter(KeyedVectors<vector_size=200, 1193514 keys>)
[info] loading wiki (this will take time)
[info] loaded wiki(KeyedVectors<vector_size=300, 400000 keys>)
Out[6]: ['madrid', 'arsenal', 'chelsea', 'milan', 'barcelona', 'bayern', 'barça']
```

For example, in the above example, it may make sense to _play around_ with the parameters of the `related` operation as shown in the next example:

```python
In [7]: R.K = 5
In [8]: R.KEEP_ALL_RELATEDNESS = 0.4
In [9]: R.process('barca') 
```
Using the above settings, which are much more relaxed than the standard settings, the following result will be generated:

```python
['guardiola', 'psg', 'espanyol', 'ronaldinho', 'juve', 'madrid', 'milan', "eto'o", 'nou', 'barça', 'arsenal', 'bayern', 'messi', 'sevilla', 'chelsea', 'barcelona', 'rijkaard']
 ```

# Further Documentation

See also [Presentation.marp.md](Presentation.marp.md) for further information.