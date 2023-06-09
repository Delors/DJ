---
marp: true
paginate: true
---

# DJ - Dictionary Juggler

**A domain-specific language (DSL) for analyzing, transforming and generating dictionaries for password recovery.**

*Dr. Michael Eichberg*  
Summer 2023

---

# Motivation

When dealing with dictionaries...

1. we want to do similar things very often
1. doing things using a combination of `tr`, `sed`, `awk`,`grep`, _shell scripts_, _python hacking_, `hashcat --stdout` is possible (at least to some extent), but neither reusable nor comprehensible (at least not after some months, weeks, days, ...)  
***Intermediate files "hell"...***
1. we want a comprehensible documentation what was done
1. we often want to generate various different output files (e.g, a base dictionary and one or more rule files.)

---

# Conceptual Idea

1. Process, i.e., transform, filter, take apart or analyze, one entry of a dictionary at a time to create the needed entries.
*This enables DJ to process arbitrary large dictionaries.*
1. Processing an entry is done by simple, basic operations.
1. Enable the processing of every entry using multiple pipelines to create, based on the same entry, all desired variants.
1. Apply (basic) operations (e.g., split, strip whitespace, lower, ...) on *all results* of the previous operation.  
*I.e., an operation may produce between zero and many (intermediate) results.*
1. Write out the results (to a file or stdout).

<!-- _footer: Some selected features require memory which scales along with the size of the dictionary.  -->

---

# Basic example (`split " " report`)

| Operation             | Input         | Output        | Remark    |
| --------------------- | ------------- | ------------- | --------- |
| `split " " `          | ["A Test"]    | ["A","Test"]  | 
| `report`              | ["A","Test"]  | ["A","Test"]  | Additionally, printed to stdout

Running it on the shell:

```sh
/DJ% echo 'A Test\nAnother Test' | ./dj.py 'split " " report'
A
Test
Another
Test
```

---

# Basic Grammar

```sh
op_seq := (<operation_name> <operation parameters>?)+

operation_name := "[a-z_]+"
operations parameters := ...defined by the operation, 
                            but the last parameter must
                            never match an operation name
                            to keep the files easily 
                            readable by humans...
```

<!-- The grammar is defined using parsing expression grammars (PEGs). -->

---

# Output

- Either a `report` or a `write` operation is required, to output the results of an operation sequence. 
- Multiple write operations to the same file are possible.
- To create pre-initialized files use the `create` directive.
- To suppress duplicates use the parameter `-u`.  
*This requires that the generated dictionary completely fits into memory!*

<!-- A `directive` is an operation at the beginning of a dj document that is executed once before the entries will be processed.-->

---

# Basic Usage

```sh
dj.py [-h] [-o OPERATIONS] [-d DICTIONARY] [-v] [-t] [-p] [--pace] [-u] [OPs ...]
```

- *Command-line usage*: the operations are directly specified and the dictionary is read from the command line:  
`echo 'A Test\nAnother Test' | ./dj.py 'split " " report'`
- *Scripted*: The operations script and (optionally) the dictionary are read from a file:  
`./dj.py -o Scripts.dj -d Towns_of_the_world.txt`

---

# An operation that does not apply will filter a given entry! 

**Apply** generally means, the operation has some effect on the given entry.

| Operation             | Input         | Output        | Remark    |
| --------------------- | ------------- | ------------- | --------- |
| `lower`         | ["amsterdam"]    | None(N/A) | No further operations will be performed!

<!-- See the documentation of the respective operations to understand the effect of apply!-->

---



# Applicable Transformers

When applying an operation, DJ distinguishes two cases: An _operation is applicable_ vs. _an operation is not applicable_; this facilitates advanced processing of entries. In particular, it enables us to continue with the processed entry if the operation was applicable and otherwise continue with the original entry.

| Operation             | Input         | Output        | Remark    |
| --------------------- | ------------- | ------------- | --------- |
| `remove "-"`         | ["---"]    | [""] | The empty string will be then ignored

| Operation             | Input         | Output        | Remark    |
| --------------------- | ------------- | ------------- | --------- |
| `remove "-"`          | ["AB"]  | (N/A)  | None will then be ignored.

<!-- footer: All filters are always considered being applicable. -->

---

# `+` Meta-Operator 


- `+` (e.g., `+remove "-"`) will ensure that the result of the operation will always contain the original entry and the results of the transformation.
- useable for Tranformers and Extractors  

---

# `*` Meta-Operator (*Continue if not applicable*)

- `*` (e.g,. `*remove " "`) will pass on the current entries set, if and only if, the operation was not applicable to all given entries.  
*Often the `*` operator is combined with an `ilist_foreach` operation.*

| Operation             | Input         | Output        | Remark    |
| --------------------- | ------------- | ------------- | --------- |
| `*remove "-"`          | ["a-b"]  | ["ab"] | 
|  |  |  |  |
| `*remove "-"`          | ["ab"]  | ["ab"] | 
|  |  |  |  |
| `*remove "-"`          | ["---"]  | [""] | The operation was applicable.

---

# `!` Meta-Operator 


- `!` (e.g., `!is_pattern`) inverts a filter operation.
- useable only by filters

---

# Basic Transformers

| Shorten       | Extends | In-place | Splits-up |
| --------------|---|-------------|---|
| remove        | append  | number | split |
| remove_sc     |  | replace | sub_split |
| deduplicate   |  | title | segments |
| deduplicate_reversed   |  | upper | |
| detriplicate   |  | lower  | |
| deleetify   |  | capitalize | |
| fold_ws  |  |  | |
| omit      |  |  | |
| strip | |  | |
| strip_ws | |  | |
| strip_no_and_sc | |  | |

---






 ---

discard_endings
theme: uncover
capitalize
lower
upper

cut

correct_spelling

is_part_of
is_sc

is_popular_word
[is_regular_word](#is_regular_word)

[mangle_dates](#mangle_dates)

---
 
# Sets

- The implicit (current) per dictionary entry set  (___ilist\_*___)
- Named sets per dictionary

---

# Intermediate Sets

Operations beginning with "ilist_" operate on the current implicit, intermediate set:
  - **Processing all current items one ofter another**: ilist_foreach      
    _Often used in combination with the "+" operator._
  - **Quantification over the intermediate set**: ilist_if_all, ilist_if_any
  - **Transformations**: ilist_concat

---

# Named Sets

- Named sets first need to be declared and then need to be populated by operations. 
- Named sets can be populated in a piece-wise manner.
- Named sets are used using the built-in `use` operation.
- Named sets are cleared after processing a dictionary entry.

Example:
```sh
set BASE
{ *strip_ws *strip_no_and_sc *split " " }> Base
use BASE report
use BASE ilist_foreach( get_no report )
```

---

# (Global) Configuration

- Many operations have per instance and also global configuration options.
- Global configuration options are used for those options that are not related to processing individual entries.


---

# **Examples**

---

# Generating Hashcat Rules for Numbers found in the Dictionary

```sh
# Global Configuration
create "append_numbers.rule" ":"
create "prepend_numbers.rule" ":"
set NUMBERS

# Operation sequences
get_no \
    min length 2 \
    { write "numbers.txt" }> NUMBERS 
use NUMBERS \
    prepend each "$"                write "append_numbers.rule"
use NUMBERS \
    reverse prepend each "^"        write "prepend_numbers.rule"
```



---

# Internal Operations

All operations which take other operations as parameters are internal operations for efficiency purposes.

---

# Operations

Operations are either, `Transformers`, `Extractors` or `Filters`.

Operations are added, extended on a per-need basis. When they are extended, this is most-often done in a backward compatible way.

---

# is_regular_word

---

# mangle_dates

---