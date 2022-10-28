# Dictionary Transformation and Generation for Password Recovery aka `Dictionary Juggling` (DJ)

Processes the entries of a _base_ dictionary by applying one to multiple user-definable transformations, extractions,  filtering or generating operations. 
Basically, DJ enables the trivial definition of user-defineable transformation pipelines to generate dictionaries useable for password recovery.

## Installation

To execute basic operations (e.g. `strip`,`remove`,`fold`,..), no special installation steps/downloads are necessary. However, to use the advanced "semantic-based" features, several dictionaries and pre-trained NLP models are required. Some will be downloaded automatically and some need to be pre-installed.

### 1. Download dictionaries
Some of the available operations need well defined dictionaries as a foundation. 
These dictionaries need to be `hunspell` dictionaries. Most operations rely on those used by [libreoffice](https://github.com/LibreOffice/dictionaries) and the dictionaries need to be placed in the folder `dicts`.

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
git clone --recurse-submodules https://github.com/scherzocrk/pynuspell.git
cd pynuspell
./extern/vcpkg/bootstrap-vcpkg.sh
export VCPKG_ROOT=./extern/vcpkg
./extern/vcpkg/vcpkg install
pip3 install .
```

### 3. Prepare for offline Usage
In general, DJ can be used offline. However, some operations (in particular `related`) require data that will be loaded on demand and will then be stored in the user's home folder. If DJ is to be used on an offline computer this data then needs to be copied to the offline machine. 

To force DJ to download the necessary data just start DJ with the `related` operation and type a single word:

```bash
$ ./DJ.py is_popular_word
Wiesbaden
``` 

## Usage

Reads in a (case) specific dictionary and generates an output dictionary by processing each input entry according to some well defined operations. Additionally, DJ can also be used to _just_ analyze existing dictionaries to filter entries.

### Basic Usage

```sh
python3 DJ.py <operations>
```

In this case a dictionary will be read from stdin and then the specified operations will be performed for each entry. 

For example, in case of `python3 DJ.py lower` every entry of the given dictionary will be converted to lower case and will then be output. Entries which are already in lower case will be ignored.

### Standard Usage

```sh
python3 DJ.py [-o <Operations File>] [-d <Dictionary.utf8.txt>]
```

Reads from standard-in or the specified file (`-d`) a dictionary and performs the operations specified in the given operations file. A default file: `default_ops.td` exists, which - however - primarily serves demonstration purposes.

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

I.e., the second `+split \s` operation is effectively useless.

### Formatting long operation definitions

To foster readability of long operation definitions it is possible to split up an operations definition over multiple lines by starting the next lines using "\ " at the beginning of a line. This is then treated as a continuation of the previous line.  Hence, the above rule (Example 2) can also be written as:

``` 
+split \s 
\ +remove_ws 
\ *map \s [-_]
\ +lower report
```

## Atomic Operations
Each atomic operation (e.g., `lower`, `min_length`, `related`, `get_numbers`) performs one well-defined transformation, extraction, filtering operation and most operations provide some level of configurability. 

### Built-in Operations
Additionally, DJ has some built-in directives for special purposes:

 - `def` to define a macro
 - `config` to configure an operation's global parameters
 - `ignore` to specify a file with terms that will always be ignored; for example, when processing a dictionary that contains names of locations (e.g., "Frankfurt an der Oder" or "Rotenburg ob der Tauber" or "South Beach" you often want to ignore specific words to avoid cluttering of the generated dictionary (here, "an", "ob", "der", or "South" are potentially candidates you want to ignore.))

Controlling the output
 - `report` to write the result of an operations sequence to stdout. 
 - `write` to write out the results of a transformation to a specific file instead of `stdout`.

(For the documentation of specific operations see the code for now.)

## Development/Debugging of Operations

A design principle of DJ is to make it possible to develop and test operations independently. For example, to test the **related** operation it is trivially possible to use a python console to instantiate the class and to then call the **related** operation as shown in the next example:

```python
/DJ% python3
In [1]: from operations.related import Related
In [2]: R = Related()
In [3]: R.process("barca")
[info] loading twitter (this will take time)
[info] loaded twitter(KeyedVectors<vector_size=200, 1193514 keys>)
[info] loading wiki (this will take time)
[info] loaded wiki(KeyedVectors<vector_size=300, 400000 keys>)
Out[3]: ['madrid', 'arsenal', 'chelsea', 'milan', 'barcelona', 'bayern', 'barça']
```

For example, in the above example, it may make sense to _play around_ with the parameters of the related operation as shown in the next example:

```python
import importlib
m = importlib.import_module("operations.related")
ClassR = getattr(m,"Related")
setattr(ClassR,"K",25)
setattr(ClassR,"KEEP_ALL_RELATEDNESS",0.75)
R = ClassR(0.3)
R.process("barca")               
```
Using the above settings, which are much more relaxed than the standard settings, the following result will be generated:

```python
['munchen',
 'messi',
 'juventus',
 'madrid',
 'ronaldo',
 'visca',
 'barcelona',
 'chelsea',
 'liverpool',
 'barça',
 'manchester',
 'ucl',
 'spanyol',
 'bayern',
 'juve',
 'fabregas',
 'malaga',
 'dortmund',
 'arsenal',
 'psg',
 'fcb',
 'guardiola',
 'inter',
 'milan',
 'atletico']
 ```
