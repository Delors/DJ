#!/usr/bin/python3

# Bundeskriminalamt KT53
# Dr. Michael Eichberg (michael.eichberg@bka.bund.de)
# (c) 2022

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

import sys
import itertools
import os
import argparse

# Uses the pip package: pyspellchecker
# TODO replace by pyenchant (and nuspell?) - with hunspell dictionaries 
from spellchecker import SpellChecker
import re

def locate_resource(filename : str) -> str:
    """ Tries to locate the file by searching for it relatively to the current
        folder or the folder where this python script is stored unless the 
        filename is already absolute.
    """
    if os.path.isabs(filename):
        return filename
    
    if os.path.exists(filename):
        return filename
    
    try:
        abs_filename = os.path.join(os.path.dirname(__file__),filename)
        if os.path.exists(abs_filename):
            return abs_filename
        else:
            error = f"neither ./{filename} nor {abs_filename} exists"
            raise FileNotFoundError(error)
    except Exception as e:
        print(f"can't locate {filename}: {e}", file=sys.stderr)
        raise


__reported_entries : Set[str] = set()
""" The set of reported, i.e., printed, entries per entry. This list is cleared
    by the `transform_entries` method after completely processing an entry.
    """

def report(s : str):
    """Prints out the entry if it was not yet printed as part of the mangling
       of the same entry.
    """
    if s not in __reported_entries:
        __reported_entries.add(s)
        print(s)


class Operation(ABC):
    """ Representation of an operation. An operation processes an entry
        and produces zero (`[]`) to many entries. An operation which 
        does not apply to an entry returns `None`. For a definition
        of "does not apply" see the documentation of the respective 
        classes of operations.

        An operation is either:
        - a transformation which takes an entry and returns between
          zero and many new entries; i.e., the original entry will
          never be returned. If a transformation does not generate
          new entries, the transformation is considered to be not
          applicable to the entry and None is returned.
          For example, if an entry only consists of special characters
          and the operation removes all special characterss, a empty 
          list (not None) will be returned.
        - an extractor which extracts one to multiple parts of an entry. 
          An extractor might "extract" the original entry. For example,
          an extractor for numbers might return the original entry if 
          the entry just consists of numbers.
          An extractor which does not extract a single entry is not
          considered to be applicable and None is returned.
        - a meta operation which manipulates the behavior of an
          extractor or a translation.
        - a filter operation which takes an entry and either returns
          the entry as is or the empty list ([]). Hence, a filter
          is considered to be always applicable.
        - a report operation which either collects some statistics or
          which prints out an entry but always just returns the entry
          as is.
        - a macro which combines one to many operations and which basically
          provides a convience method to facilitate the definition of
          operations which should be carried out in a specific order.
    """

    @abstractmethod
    def process(self, entry: str) -> List[str]:
        """
        Processes the given entry and returns the list of new entries.
        If an operation applies, i.e., the operation can meangingfully
        be applied, a list of new entries (possibly empty) will be returned.
        If an operation does not apply at all, None should be returned.
        Each operation has to clearly define when it applies and when not.

        For example, an operation to remove special chars would apply to
        an entry consisting only of special chars and would return
        the empty list in that case. If, however, the entry does not 
        contain any special characters, None would be returned.

        E.g., an operation that just extracts certain characters or which 
        replaces certain characters will always either return a 
        non-empty list (`[]`) or `None` (didn't apply).
        """
        pass

    def is_transformer(self) -> bool: return False

    def is_extractor(self) -> bool: return False    

    def is_meta_op(self) -> bool: return False

    def is_macro(self) -> bool: return False

    def is_reporter(self) -> bool: return False        

    def is_filter(self) -> bool: return False                


ignored_entries = set()
""" The global list of all entries which will always be ignored.
    Compared to an operation which only processes an entry at
    a specific point in time, an entry will - after each step -
    always be checked against entries in the ignored_entries set.
"""


def apply_ops(entry : str, ops : List[Operation]) -> List[str]:
    """ Applies all operations to the given entry. As a result multiple new 
        entries may be generated. None is returned if and only if the 
        application of an operation to all (intermediate) entries results in 
        `None`.
    """
    
    entries = [entry]    
    for op in ops:
        all_none = True
        new_entries = []
        for entry in entries:
            if len(entry) > 0:
                try:
                    new_candidate_entries = op.process(entry)
                    if new_candidate_entries is not None:
                        all_none = False
                        for new_entry in new_candidate_entries:
                            if new_entry not in ignored_entries:
                                new_entries.append(new_entry)
                except Exception as e:
                    print(f"operation {op} failed: {e}",file=sys.stderr)
                    raise
        entries = new_entries

        if len(entries) == 0:
            if all_none:
                return None
            else:
                return []

    return entries


class Report(Operation):
    """The "report" operation prints out the entry. 

    A report generally terminates a sequence of operations, but it
    can also be used if an intermediate result is actually a desired 
    output and we do not want to have multiple operations. For example:

    report ___remove\_ws capitalize report___

    In the above case, we first print out the (original) entry, after
    that white space is removed which will also filter the set of 
    entries down to those which had white space in the first place 
    and then those entries will be capitalized. For example,
    given the two entries:

        TestTest
        Dies ist ein Test

    the output will be:

        TestTest            [output due to initial report]
        Dies ist ein Test   [output due to initial report]
        Diesisteintest      [after removing ws and capitalization]

    notably:
    
        Testtest
        DiesisteinTest
    
    will not be output.
    """

    def is_reporter(self) -> bool: return True   

    def process(self, entry: str) -> List[str]:
        report(entry)
        return [entry]

    def __str__(self):
        return "report"

REPORT = Report()        


class Macro(Operation):
    """Definition of a macro."""

    def __init__(self, name :str, ops : List[Operation]):
        self.name = name
        self.ops = ops
        return

    def is_macro(self) -> bool: 
        return True

    def process(self, entry: str) -> List[str]:
        return apply_ops(entry,self.ops)

    def __str__(self):
        return self.name


class KeepAlwaysModifier(Operation):
    """ Modifies the behavior of the wrapped transformer/extractor
        such that all input entries will also be output entries 
        additionally to those that are newly created by the 
        wrapped operation.
    """

    def __init__(self, op : Operation):
        self.op = op

        if not op.is_transformer() and not op.is_extractor():
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = []
        entries.append(entry)
        return entries
        
    def __str__(self):
        return "+" + str(self.op)


class KeepOnlyIfFilteredModifier(Operation):
    """ Modifies the behavior of the wrapped operation such that an
        input entry will be an output entry if the wrapped operation
        does not apply to the entry. I.e., if the wrapped operation 
        returns None, the entry is passed on otherwise the result
        of the wrapped operation is passed on as is.
    """

    def __init__(self, op : Operation):
        self.op = op

        if not (op.is_transformer() or op.is_extractor()):
            raise ValueError(f"unsupported base operation: {op}")

        return

    def process(self, entry: str) -> List[str]:
        entries = self.op.process(entry)
        if entries is None:
            entries = [entry]
        return entries
        
    def __str__(self):
        return "*" + str(self.op)        


class DeLeetify(Operation):
    """ Deleetifies an entry by replacing the used numbers with their
        respective characters. E.g., *T3st* is deleetified to _Test_. To avoid
        the creation of irrelevant entries, a spellchecker is used to test 
        that the deleetified word is a real world. Please note, that using
        a spellchecker directly to deleetify a word will generally not work
        for heavily leetified words, e.g., _T4553_, which might stand for 
        _Tasse_ in German.

        Currently, deleetification is only supported for the following
        languages: "de", "en" and "fr"; capitalization is
        ignored. Additionally, we currently only deleetify words containing
        a, e, i and o.
    """

    """
    mappings = {
            ("0","o"),
            ("3","e"),
            ("4","a"),
            ("1","i")
        }
    """
    """ Currently not used transliterations:
            [("5","s")],
            [("6","g")],
            [("7","t")],
            [("8","b")],
            [("1","l")],
            [("2","r"),("2","z")],
            [("4","h")],
            [("9","p"),("9","g")]"""

    replacements = list(
        itertools.chain.from_iterable(
            itertools.combinations({
                ("0","o"),
                ("1","i"),
                ("3","e"),
                ("4","a")                
            },l) for l in range(1,4)
        )
    )

    # REs to test if we have leetspeak. The REs are based on the assumption that
    # we never have words with more than three subsequent vowles and that the
    # numbers 0,3,4,1 are the only relevant ones.
    # (In reality such words exists; e.g. Aioli !)
    _re_has_at_least_one_seq_with_at_most_three_numbers = re.compile("[^0-9]*[0134]{1,3}([^0-9]|$)")
    _re_has_leetspeak = re.compile(".*[a-zA-Z]")

    spell_en = SpellChecker(language="en")
    known_en = spell_en.known 
    spell_de = SpellChecker(language="de")
    known_de = spell_de.known
    spell_fr = SpellChecker(language="fr")
    known_fr = spell_fr.known

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        # (See Wikipedia for more details!) We currently only consider
        # the basic visual transliterations related to numbers and
        # we assume that a user only uses one specific transliteration
        # if multiple alternatives exists. I.e., a word such as _Hallo_
        # will either be rewritten as: _4allo_ or _H4llo_ or _H411o_, but 
        # will never be rewritten to _44llo_. In the last case, the mapping is
        # no longer bijective. Additionally, we assume that a user uses
        # at most three transliterations and only transliterates vowels. 
        # The last two decisions are made based on "practical" observations
        # and to keep the computational overhead reasonable.

        # The following tests are just an optimization:
        if  not DeLeetify._re_has_at_least_one_seq_with_at_most_three_numbers.match(entry) or\
            not DeLeetify._re_has_leetspeak.match(entry):
            return None

        # TODO [IMPROVEMENT] First scan for all numbers in the entry and then perform the relevant transformations instead of testing all combinations of transformations.

        deleetified_entries : Set[str] = set()
        for rs in DeLeetify.replacements:
            deleetified_entry = entry
            for (n,c) in rs:
                deleetified_entry = deleetified_entry.replace(n,c)
            if entry != deleetified_entry:
                deleetified_entries.add(deleetified_entry)


        deleetified_words : List[str] = []

        for deleetified_entry in deleetified_entries:

            deleetified_terms = deleetified_entry.split()
            terms_count =  len(deleetified_terms)

            # alternative test: all(len(known_en([t])) != 0 for t in deleetified_terms)\
            if  len(DeLeetify.known_en(deleetified_terms)) == terms_count\
                or\
                len(DeLeetify.known_de(deleetified_terms)) == terms_count\
                or\
                len(DeLeetify.known_fr(deleetified_terms)) == terms_count:
                deleetified_words.append(deleetified_entry)
        
        if len(deleetified_entries) == 0:
            return None
        else:
            return deleetified_words

    def __str__(self):
        return "deleetify"

DELEETIFY = DeLeetify()   


class RemoveWhitespace(Operation):
    """Removes all whitespace."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        split_entries = entry.split()
        if len(split_entries) == 0:
            # The entry consisted only of WS
            return []
        elif len(split_entries) == 1:  
            return None
        else:
            return ["".join(split_entries)]

    def __str__(self):
        return "remove_ws"

REMOVE_WHITESPACE = RemoveWhitespace()        


class Strip(Operation):
    """Removes leading and trailing whitespace."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        stripped_entry = entry.strip()
        if stripped_entry is entry:
            return None
        elif len(stripped_entry) == 0:
            # The entry just consisted of WS
            return []
        else: # stripped_entry != entry:
            # The entry is not empty
            return [stripped_entry]

    def __str__(self):
        return "strip"

STRIP = Strip()    


class ToLower(Operation):
    """Converts an entry to all lower case."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        lower = entry.lower()
        if lower != entry:
            return [lower]
        else:
            return None

    def __str__(self):
        return "to_lower"    

TO_LOWER = ToLower()            


class ToUpper(Operation):
    """Converts an entry to all upper case."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        upper = entry.upper()
        if upper != entry:
            return [upper]
        else:
            return None

    def __str__(self):
        return "to_upper"    

TO_UPPER = ToUpper()   


class RemoveSpecialChars(Operation):
    """ Removes all special chars; whitespace is not considered as a
        special char. In general it is recommend to remove whitespace
        and/or strip the entries afterwards.
    """

    #re_non_special_char = re.compile("[a-zA-Z0-9\s]+")
    re_non_special_char = re.compile(
        "[^<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-]+"
        )

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveSpecialChars.re_non_special_char.finditer(entry)
        ]
        if len(entries) == 0:
            # the entry just consisted of special chars...
            return []
        elif entry != entries[0]:
            return ["".join(entries)]
        else:
            # there were no special chars
            return None

    def __str__(self):
        return "remove_sc"

REMOVE_SPECIAL_CHARS = RemoveSpecialChars()


class GetSpecialChars(Operation):
    """Extracts the used special char (sequences)."""

    #re_special_chars = re.compile("[^a-zA-Z0-9\s]+")
    re_special_chars = "[<>|,;.:_#'+*~@€²³`'^°!\"§$%&/()\[\]{}\\\-]+"

    def is_extractor(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetSpecialChars.re_special_chars.finditer(entry)
        ]
        if len(entries) >= 1:
            return entries
        else:
            return None

    def __str__(self):
        return "get_sc"

GET_SPECIAL_CHARS = GetSpecialChars()


class GetNumbers(Operation):
    """Extracts all numbers."""

    re_numbers = re.compile("[0-9]+")

    def is_extractor(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetNumbers.re_numbers.finditer(entry)
        ]
        if len(entries) >= 1:
            return entries
        else:
            return None

    def __str__(self):
        return "get_numbers"   

GET_NUMBERS = GetNumbers()


class RemoveNumbers(Operation):
    """Removes all numbers from an entry."""

    re_no_numbers = re.compile("[^0-9]+")

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveNumbers.re_no_numbers.finditer(entry)
        ]
        if len(entries) == 0:
            return []
        elif entry != entries[0]:
            return ["".join(entries)]
        else:
            return None

    def __str__(self):
        return "remove_numbers"   

REMOVE_NUMBERS = RemoveNumbers()


class FoldWhitespace(Operation):
    """ Folds multiple whitespace (spaces and tabs) to one space."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        last_entry = ""
        folded_entry = entry
        while folded_entry != last_entry:
            last_entry = folded_entry
            folded_entry = folded_entry\
                .replace("  "," ")\
                .replace("\t"," ") # May result in 2 or 3 subsequent spaces
        if entry != folded_entry:
            return [folded_entry]
        else:
            return None

    def __str__(self):
        return "fold_ws"

FOLD_WHITESPACE = FoldWhitespace()


class Capitalize(Operation):
    """Capitalizes a given entry."""

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return None

    def __str__(self):
        return "capitalize"

CAPITALIZE = Capitalize()


class MinLength(Operation):
    """Only accepts entries with a given minimum length."""

    def __init__(self, min_length : int):
        self.min_length = min_length
        return

    def is_filter(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if len(entry) >= self.min_length:
            return [entry]
        else:
            return []

    def __str__(self):
        return f"min_length {self.min_length}"

class MaxLength(Operation):
    """Only accepts entries with a given maximum length."""

    def __init__(self, max_length : int):
        self.max_length = max_length
        return

    def is_filter(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if len(entry) <= self.max_length:
            return [entry]
        else:
            return []

    def __str__(self):
        return f"max_length {self.max_length}"

class MangleDates(Operation):
    """ Tries to identify numbers which are dates and then creates various
        representations for the respective date.

        Currently, we try to identify german and english dates.
    """

    re_german_date = re.compile("[^0-9]*([0-9]{1,2})\.?([0-9]{1,2})\.?(19|20)?([0-9]{2})")
    re_english_date = re.compile("[^0-9]*([0-9]{1,2})[/-]?([0-9]{1,2})[/-]?(19|20)?([0-9]{2})")    

    def __init__(self): pass

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        r = MangleDates.re_german_date.match(entry)
        if r:
            (d,m,c,y) = r.groups()
        else:
            r = MangleDates.re_english_date.match(entry)
            if r:
                (m,d,c,y) = r.groups()

        if not r:    
            return None

        """Currently we only accept dates between 1975 and 2025.
            The test ist not extremely precise, but should be acceptable for
            our purposes.
        """
        if int(d) > 31 or int(d) == 0 or int(m) > 12 or int(m) == 0 or (int(y) > 25 and int(y) < 75) or (c and (c == 19 or c == 20)):
            return []

        mangled_dates = [d+m+y,y]
        if c:
            mangled_dates.append(d+m+c+y)
            mangled_dates.append(c+y)
        else:
            if int(y) <= 25:
                mangled_dates.append("20"+y)
            else:
                mangled_dates.append("19"+y)

        if len(d) == 1:
            if len(m) == 1:
                mangled_dates.append("0"+d+"0"+m+y)
                mangled_dates.append("0"+d+"0"+m)
                mangled_dates.append("0"+m+"0"+d)
            else:
                mangled_dates.append("0"+d+m+y)
                mangled_dates.append("0"+d+m)
                mangled_dates.append(m+"0"+d)
        else:
            if len(m) == 1:
                mangled_dates.append(d+"0"+m+y)
                mangled_dates.append(d+"0"+m)
                mangled_dates.append("0"+m+d)
            else:
                mangled_dates.append(d+m)
                mangled_dates.append(m+d)

        return mangled_dates
            

    def __str__ (self):
        return "mangle_dates"

MANGLE_DATES = MangleDates()      


class Split(Operation):
    """ Splits up an entry using the given split_char as a separator.
    """

    def __init__(self, split_char : str):
        self.split_char = split_char
        return

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        assert len(entry) > 0

        all_segments = entry.split(self.split_char)
        # all_segments will have at least two elements
        # if a split char is found
        if len(all_segments) == 1:
            return None
                
        segments = list(filter(lambda e: len(e) > 0, all_segments))
        return segments

    def __str__ (self):
        split_char_def = self.split_char\
            .replace(' ',"\\s")\
            .replace('\t',"\\t")
        return f"split {split_char_def}"         


class Number(Operation):
    """ Replaces every matched character by the number 
        of previous occurrences of matched characters.

        E.g. if the _chars to number_ set consists of [aeiou] and
        the string "Bullen jagen" is given, then the result of the
        transformation is: "B1ll2n j3g4n".
    """

    def __init__(self, chars_to_number : str):
        self.chars_to_number = set(chars_to_number) 
        return

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        count = 0
        new_e = ""
        for e in entry:
            if e in self.chars_to_number:
                count += 1
                new_e += str(count)
            else:
                new_e += e

        if count == 0:
            return None
        else:
            return [new_e]

    def __str__ (self):
        chars = "".join(self.chars_to_number)
        return f"number [{chars}]"


class Map(Operation):
    """ Maps a given character to several alternatives.
    """

    def __init__(self, source_char : str, target_chars : str):
        self.source_char = source_char
        self.target_chars = set(target_chars) 
        return

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        if self.source_char in entry:
            entries = []
            for c in self.target_chars:
                entries.append(entry.replace(self.source_char,c))
            return entries
        else:
            return None        

    def __str__ (self):
        # TODO Escape
        source_char = self.source_char
        target_chars = "".join(self.target_chars)
        return f"maps {source_char} [{target_chars}]"


class SubSplits(Operation):
    """ Splits up an entry using the given split_char as a separator
        creating all possible sub splits, keeping the order.
        E.g. Abc-def-ghi with - as the split char would create:
            Abc-def
            def-ghi
            Abc-ghi
    """

    def __init__(self, split_char : str):
        self.split_char = split_char
        return

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]:
        assert len(entry) > 0

        all_segments = entry.split(self.split_char)
        
        all_segments_count = len(all_segments)
        # Recall that, when the split char appears at least once,
        # we will have at least two segments.
        if all_segments_count == 1:            
            return None

        segments = filter(lambda e: len(e) > 0, all_segments)    
        segments_count = len(segments)
        if segments_count == 0:
            # the entry just consisted of the split character
            return []    

        entries = []
        for i in range(2,segments_count):
            entries.append(self.split_char.join(segments[0:i]))
        for i in range(1,segments_count-1):
            entries.append(self.split_char.join(segments[i:segments_count]))

        entries.extend(segments)            
        return entries
            
    def __str__ (self):
        split_char_def = self.split_char\
            .replace(' ',"\\s")\
            .replace('\t',"\\t")
        return f"sub_splits {split_char_def}"           
  

class Replace(Operation):
    """Replaces a character by another (set of) character(s)."""

    def __init__(self, replacements_filename):
        self.replacements_filename = replacements_filename
        abs_filename = locate_resource(replacements_filename)
        
        replacement_table : dict[str,str] = {}
        with open(abs_filename,"r", encoding='utf-8') as replace_file :
            for line in replace_file:
                sline = line.strip()
                if len(sline) == 0 or sline.startswith("# "):
                    continue
                (raw_key,raw_value) = sline.split()
                key = raw_key\
                    .replace("\\s"," ")\
                    .replace("\#","#")\
                    .replace("\\\\","\\")
                value = raw_value\
                    .replace("\\s"," ")\
                    .replace("\#","#")\
                    .replace("\\\\","\\")
                current_values = replacement_table.get(key)       
                if current_values:
                    raise SyntaxError                    
                else:
                    replacement_table[key] = value        
        self.replacement_table = replacement_table

    def is_transformer(self) -> bool: return True

    def process(self, entry: str) -> List[str]: 
        e = entry       
        for k,v in self.replacement_table.items():
            # RECALL:   Replace maintains object identity if there is 
            #           nothing to replace.    
            e = e.replace(k,v) 
        if entry is e:            
            return None
        else:
            return [e]
        
    def __str__(self):
        return f'replace "{self.replacements_filename}"'


class DiscardEndings(Operation):
    """
    Discards the last term - recursively - of a string with multiple elements
    if the term is defined in the given file. The preceeding 
    whitespace will also be discarded.
    
    For example, given the string:

        _Michael ist ein_

    and assuming that "ist" and "ein" should not be endings, the only
    string that will pass this operation would be "Michael".
    """

    def __init__(self, endings_filename):
        self.endings_filename = endings_filename

        endings : Set[str] = set()
        endings_ressource = locate_resource(endings_filename)
        with open(endings_ressource,"r",encoding="utf-8") as fin :
            for ending in fin:
                endings.add(ending.rstrip("\r\n"))       
        self.endings = endings

    def is_transformer(self) -> bool: return True        

    def process(self, entry: str) -> List[str]: 
        all_terms = entry.split()
        count = 0
        while len(all_terms) > (-count) and \
              all_terms[count -1] in self.endings:
            count -= 1

        if count != 0:
            return [" ".join(all_terms[0:count])]
        else:
            return None
        
    def __str__(self):
        return f'discard_endings"{self.endings_filename}"'


class ComplexOperation:
    """ Representation of a complex operation.

        Instantiation of a complex operation which is made up of 
        multiple atomic operations. An instance of ComplexOperation 
        basically just handles applying the atomic operations to 
        an entry and (potentially) every subsequently created entry.
    """

    def __init__(self, ops: List[Operation]):
        if not ops or len(ops) == 0:
            raise ValueError(f"no operations specified: {ops}")

        self.ops = ops
        return

    def apply(self, entry):
        return apply_ops(entry,self.ops)

    def __str__(self) -> str:
        return " ".join(map(str,self.ops))


### PARSER SETUP AND CONFIGURATION

re_next_word = re.compile("^[^\s]+")
re_next_quoted_word = re.compile('^"[^"]+"')

def parse(operation) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations without parameters."""

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        return (rest_of_op,operation)

    return parse_it   

def parse_min_length(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    min_length_match = re_next_word.match(rest_of_op)
    min_length = int(min_length_match.group(0))
    new_rest_of_op = rest_of_op[min_length_match.end(0):].lstrip()
    return (new_rest_of_op,MinLength(min_length))

def parse_max_length(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    max_length_match = re_next_word.match(rest_of_op)
    max_length = int(max_length_match.group(0))
    new_rest_of_op = rest_of_op[max_length_match.end(0):].lstrip()
    return (new_rest_of_op,MaxLength(max_length))

def parse_number(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    chars_to_number_match = re_next_word.match(rest_of_op)
    raw_chars_to_number = chars_to_number_match.group(0)
    chars_to_number = raw_chars_to_number \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    new_rest_of_op = rest_of_op[chars_to_number_match.end(0):].lstrip()
    return (new_rest_of_op,Number(chars_to_number[1:-1] ))# get rid of the set braces "[" and "]".

def parse_map(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    source_char_match = re_next_word.match(rest_of_op)
    raw_source_char = source_char_match.group(0)
    source_char = raw_source_char \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    rest_of_op = rest_of_op[source_char_match.end(0):].lstrip()

    target_chars_match = re_next_word.match(rest_of_op)
    raw_target_chars = target_chars_match.group(0)
    target_chars = raw_target_chars \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    new_rest_of_op = rest_of_op[target_chars_match.end(0):].lstrip()

    return (new_rest_of_op,Map(source_char,target_chars[1:-1]))    

def parse_split(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    split_chars_match = re_next_word.match(rest_of_op)
    raw_split_chars = split_chars_match.group(0)
    split_char = raw_split_chars \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    new_rest_of_op = rest_of_op[split_chars_match.end(0):].lstrip()
    return (new_rest_of_op,Split(split_char))

def parse_sub_splits(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    split_chars_match = re_next_word.match(rest_of_op)
    raw_split_chars = split_chars_match.group(0)
    split_char = raw_split_chars \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    new_rest_of_op = rest_of_op[split_chars_match.end(0):].lstrip()
    return (new_rest_of_op,SubSplits(split_char))

def parse_replace(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    replace_filename_match = re_next_quoted_word.match(rest_of_op)
    replace_filename = replace_filename_match.group(0).strip("\"")
    new_rest_of_op = rest_of_op[replace_filename_match.end(0):].lstrip()
    return (new_rest_of_op,Replace(replace_filename))

def parse_discard_endings(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    endings_filename_match = re_next_quoted_word.match(rest_of_op)
    if not endings_filename_match:
        raise Exception("discard_endings: file name missing (did you forgot the quotes(\")?)")
    endings_filename = endings_filename_match.group(0).strip("\"")
    new_rest_of_op = rest_of_op[endings_filename_match.end(0):].lstrip()    
    return (new_rest_of_op,DiscardEndings(endings_filename))


macro_defs : Tuple[str,ComplexOperation] = { }

"""Mapping between the name of an op and it's associated parameters parser."""
operation_parsers = {

    "report": parse(REPORT),
    
    # FILTERS
    "max_length": parse_max_length,
    "min_length": parse_min_length,

    # EXTRACTORS
    "get_numbers": parse(GET_NUMBERS),
    "get_sc": parse(GET_SPECIAL_CHARS),

    # TRANSFORMERS
    "fold_ws": parse(FOLD_WHITESPACE),
    "to_lower": parse(TO_LOWER),
    "to_upper": parse(TO_UPPER),
    "remove_numbers": parse(REMOVE_NUMBERS),
    "remove_ws": parse(REMOVE_WHITESPACE),
    "remove_sc": parse(REMOVE_SPECIAL_CHARS),
    "capitalize" : parse(CAPITALIZE),
    "deleetify" : parse(DELEETIFY),
    "strip" : parse(STRIP),
    "mangle_dates" : parse(MANGLE_DATES),
    "number": parse_number,
    "map": parse_map,
    "split": parse_split,
    "sub_splits": parse_sub_splits,
    "replace" : parse_replace,
    "discard_endings" : parse_discard_endings,
}


def parse_rest_of_op(previous_ops : List[Operation], line_number, rest_of_op : str) -> Tuple[str, Operation]:
    # Get name of operation parser
    next_op_parser_match = re_next_word.match(rest_of_op)
    next_op_parser_name = next_op_parser_match.group(0)

    # Check for operation modifiers (i.e. Metaoperations)
    keep_always = (next_op_parser_name[0] == "+")                
    keep_if_filtered = (next_op_parser_name[0] == "*") 
    if keep_always or keep_if_filtered:
        next_op_parser_name = next_op_parser_name[1:]

    result : Tuple[str, Operation] = None
    next_op_parser = operation_parsers.get(next_op_parser_name)
    if next_op_parser is not None:
        new_rest_of_op = rest_of_op[next_op_parser_match.end(
            0):].lstrip()
        result = next_op_parser(next_op_parser_name, new_rest_of_op)
    elif macro_defs.get(next_op_parser_name) is not None:
        macro_def = macro_defs.get(next_op_parser_name)
        new_rest_of_op = rest_of_op[next_op_parser_match.end(
            0):].lstrip()
        result = (
            new_rest_of_op,
            Macro(next_op_parser_name,macro_def.ops)
        )
    else:
        print(
            f"[error][{line_number}] unknown command: {next_op_parser_name}", 
            file=sys.stderr
        )
        return None        

    if keep_always:
        (new_rest_of_op,base_op) = result
        result = (new_rest_of_op,KeepAlwaysModifier(base_op))
    if keep_if_filtered:
        (new_rest_of_op,base_op) = result
        result = (new_rest_of_op,KeepOnlyIfFilteredModifier(base_op))
    
    return result
    


def parse_op(line_number : int, is_def : bool, sline : str) -> ComplexOperation :
    # Parse a single operation definition in collaboration with the
    # respective atomic parsers.
    atomic_ops: List[Operation] = []
    while len(sline) > 0:
        parsed_atomic_op = parse_rest_of_op(atomic_ops, line_number, sline)
        if parsed_atomic_op:
            (sline, atomic_op) = parsed_atomic_op
            atomic_ops.append(atomic_op)
            if  not is_def and\
                len(sline) == 0 and\
                not (
                    isinstance(atomic_op,Report) 
                    or 
                    (   isinstance(atomic_op,Macro) 
                        and 
                        isinstance(atomic_op.ops[-1],Report)
                    )
                ):
                print(
                    f"[info][{line_number}] adding report at the end", 
                    file=sys.stderr
                )
                atomic_ops.append(Report())
        else:
            # If the parsing of an atomic operation fails, we just
            # ignore the line as a whole.
            print(
                    f"[error][{line_number}] parsing failed: {sline}", 
                    file=sys.stderr
                )
            return None

    return ComplexOperation(atomic_ops)


def parse_ops(ops_filename : str, verbose : bool) -> List[ComplexOperation]:
    """ Parses operation definitions together with atomic operations parsers. 

        The split between the generic parser and the atomic operations parsers 
        is as follows:
        This method parses the next word to determine the next atomic operation;
        the atomic operation is then responsible for parsing its parameters and
        removing them from the string.
    """

    ops: List[ComplexOperation] = []

    abs_filename = locate_resource(ops_filename)
    with open(abs_filename, 'r', encoding='utf-8') as ops_file:
        line_number = 0
        for op_def in ops_file.readlines():
            line_number = line_number + 1
            sline = op_def.strip()

            # ignore comments and empty lines
            if sline.startswith('#') or len(sline) == 0:
                continue

            # parse ignore statement
            elif sline.startswith("ignore"):
                filename = sline[len("ignore")+1:].strip()

                if filename[0] != "\"" or filename[len(filename)-1] != "\"":
                    raise Exception("the filename has to be quoted (\")")

                abs_filename = locate_resource(filename[1:-1])
                with open(abs_filename,"r", encoding='utf-8') as fin:
                    for ignore_entry in fin:
                        # We want to be able to strip words with spaces
                        # at the beginning or end.
                        stripped_ignore_entry = ignore_entry.rstrip("\r\n")
                        if len(stripped_ignore_entry) > 0:
                            ignored_entries.add(stripped_ignore_entry)

            # parse macro definitions
            elif sline.startswith("def"):
                macro_def = sline[len("def")+1:]
                macro_name_match = re_next_word.match(macro_def)
                macro_name = macro_name_match.group(0)
                macro_body = macro_def[macro_name_match.end(0):].lstrip()
                if macro_name.upper() != macro_name:
                    raise Exception(f"macro names need to be upper case: {macro_name}")
                op = parse_op(line_number, True, macro_body)
                if op:
                    macro_defs[macro_name] = op

            # parse an operation definition
            else:
                op = parse_op(line_number, False, sline)
                if op:
                    ops.append(op)

    return ops


def transform_entries(dict_filename: str, verbose : bool, ops: List[ComplexOperation]):
    """Transforms the entries of a given dictionary."""
    d_in = None
    if dict_filename:
        d_in = open(dict_filename, "r")
    else:
        d_in = sys.stdin
    
    count = 0
    for entry in d_in:
        count = count + 1
        sentry = entry.rstrip("\r\n") # stripped entry
        if sentry not in ignored_entries:
            __reported_entries.clear()
            for op in ops:
                if verbose:
                    escaped_sentry = sentry\
                        .replace("\\","\\\\")\
                        .replace("\"","\\\"")
                    print(
                        f'[{count}:"{escaped_sentry}"] applying: {op}',
                        file=sys.stderr
                    )            
                op.apply(sentry)            


def main() -> int:
    parser = argparse.ArgumentParser(
        description=
        """Generates an attack dictionary based on a plain dictionary."""
    )
    parser.add_argument(
        '-o', 
        '--operations', 
        help="a .td file with the operations that will be applied to the dictionary entries", 
        default="default_ops.td"
    )
    parser.add_argument(
        '-d', 
        '--dictionary', 
        help="the input dictionary (if not specified stdin is used)"
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help="prints extensive trace information", 
        action="store_true"
    )
    args = parser.parse_args()

    all_operations = parse_ops(args.operations, args.verbose)
    
    transform_entries(args.dictionary, args.verbose, all_operations)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
