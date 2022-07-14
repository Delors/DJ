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
            raise Exception("neither ./{filename} nor {abs_filename} exists")

    except Exception as e:
        print(f"can't locate {filename}: {e}", file=sys.stderr)


reported_entries : Set[str] = set()
""" The set of reported, i.e., printed, entries per entry. This list is cleared
    by the `transform_entries` method after processing an entry.
    """


def report(s : str):
    """Prints out the entry."""
    if s not in reported_entries:
        reported_entries.add(s)
        print(s)


class AtomicRule(ABC):
    """Representation of an atomic rule.
    
    An atomic rule performs a single well-defined transformation.
    Every rule also acts as a filter and will only
    return those entries which are newly created as a result of the
    transformation. 
    
    The only exception is the KeepEntryModifier which
    acts like a modifier ("+" directly before the rule name) 
    and is implemented as a wrapper.    
    """

    @abstractmethod
    def process(self, entry: str) -> List[str]:
        pass


ignored_entries = set()
"""The global list of all entries which will always be ignored."""


def apply_rules(entry : str, rules : List[AtomicRule]) -> List[str]:
    """Applies all rules to the given entry. As a result multiple new 
       entries may be generated. 
    """
    entries = [entry]
    for r in rules:
        if len(entries) == 0:
            break

        new_entries = []
        for entry in entries:
            if len(entry) > 0:
                try:
                    for new_entry in r.process(entry):
                        if new_entry not in ignored_entries:
                            new_entries.append(new_entry)
                except Exception as e:
                    print(f"rule {r} failed: {e}",file=sys.stderr)
        entries = new_entries

    return entries


class Report(AtomicRule):
    """The "report" rule prints out the entry. 

    Prints out the current state of the transformation of an entry.
    Can also be used if an intermediate result is actually a desired 
    output and we do not want to have multiple rules. For example:

    ___remove\_ws +report replace "UmlautToAscii" report___

    In the above case, the first rule removes all whitespace, after that
    the +report rule will print out all entries newly created by the remove_ws
    rule and will then pass (_+_) those elements to the replace rule.
    """
    def process(self, entry: str) -> List[str]:
        report(entry)
        return []

    def __str__(self):
        return "report"

REPORT = Report()        


class Macro(AtomicRule):
    """Definition of a macro."""

    def __init__(self, name :str, rules : List[AtomicRule]):
        self.name = name
        self.rules = rules
        return

    def process(self, entry: str) -> List[str]:
        return apply_rules(entry,self.rules)

    def __str__(self):
        return self.name


class KeepAlwaysModifier(AtomicRule):
    """Modifies the behavior of the wrapped rule such that all
       input entries will also be output entries additionally
       to those that are newly created by the wrapped rule."""

    def __init__(self, rule : AtomicRule):
        self.rule = rule
        return

    def process(self, entry: str) -> List[str]:
        entries = self.rule.process(entry)
        entries.append(entry)
        return entries
        
    def __str__(self):
        return "+" + str(self.rule)


class KeepOnlyIfFilteredModifier(AtomicRule):
    """Modifies the behavior of the wrapped rule such that an
       input entry will be an output entry if the wrapped rule
       completely rejects the entry. I.e., if the wrapped rule does not
       apply, the entry is passed on.
    """

    def __init__(self, rule : AtomicRule):
        self.rule = rule
        return

    def process(self, entry: str) -> List[str]:
        entries = self.rule.process(entry)
        if len(entries) == 0:
            entries = [entry]
        return entries
        
    def __str__(self):
        return "*" + str(self.rule)        


class DeLeetify(AtomicRule):
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
                ("3","e"),
                ("4","a"),
                ("1","i")
            },l) for l in range(1,4)
        )
    )

    # REs to test if we have leetspeak. The REs are based on the assumption that
    # we never have words with more than three subsequent vowles and that the
    # numbers 0,3,4,1 are the only relevant ones.
    # (In reality such words exists; e.g. Aioli !)
    _re_has_at_least_one_seq_with_at_most_three_numbers = re.compile("[^0-9]*[0341]{1,3}([^0-9]|$)")
    _re_has_leetspeak = re.compile(".*[a-zA-Z]")

    spell_en = SpellChecker(language="en")
    known_en = spell_en.known 
    spell_de = SpellChecker(language="de")
    known_de = spell_de.known
    spell_fr = SpellChecker(language="fr")
    known_fr = spell_fr.known

    def process(self, entry: str) -> List[str]:
        # see Wikipedia for details; we currently only consider
        # the basic visual transliterations related to numbers and
        # we assume that a user only uses one specific transliteration
        # if multiple alternatives exists. I.e., a word such as _Hallo_
        # will either be rewritten as: _4allo_ or _H4llo_ or _H411o_, but 
        # will never be rewritten to _44llo_. In the last case the mapping is
        # no longer bijective. Additionally, we assume that a user uses
        # at most three transliterations and only transliterates vowels. 
        # The last two decisions are made based on "practical" observations
        # and to keep the computational overhead reasonable.

        # The following tests are just an optimization:
        if  not DeLeetify._re_has_at_least_one_seq_with_at_most_three_numbers.match(entry) or\
            not DeLeetify._re_has_leetspeak.match(entry):
            return []


        deleetified_entries : List[str] = []
        for rs in DeLeetify.replacements:
            deleetified_entry = entry
            for (n,c) in rs:
                deleetified_entry = deleetified_entry.replace(n,c)
        if entry == deleetified_entry:
            # There is no leet speak...
                continue

        deleetified_terms = deleetified_entry.split()
     
        # alternative test: all(len(known_en([t])) != 0 for t in deleetified_terms)\
            if  len(DeLeetify.known_en(deleetified_terms)) == len(deleetified_terms)\
            or\
                len(DeLeetify.known_de(deleetified_terms)) == len(deleetified_terms)\
                or\
                len(DeLeetify.known_fr(deleetified_terms)) == len(deleetified_terms):
                deleetified_entries.append(deleetified_entry)
        
        return deleetified_entries

    def __str__(self):
        return "deleetify"

DELEETIFY = DeLeetify()   


class RemoveWhitespace(AtomicRule):
    """Removes all whitespace."""

    def process(self, entry: str) -> List[str]:
        split_entries = entry.split()
        if len(split_entries) == 1:  
            return []
        else:
            return ["".join(split_entries)]

    def __str__(self):
        return "remove_ws"

REMOVE_WHITESPACE = RemoveWhitespace()        


class Strip(AtomicRule):
    """Removes leading and trailing whitespace."""

    def process(self, entry: str) -> List[str]:
        stripped_entry = entry.strip()
        if stripped_entry != entry:
            return [stripped_entry]
        else:
            return []

    def __str__(self):
        return "strip"

STRIP = Strip()    


class ToLower(AtomicRule):
    """Converts an entry to all lower case."""

    def process(self, entry: str) -> List[str]:
        lower = entry.lower()
        if lower != entry:
            return [lower]
        else:
            return []

    def __str__(self):
        return "to_lower"    

TO_LOWER = ToLower()            


class ToUpper(AtomicRule):
    """Converts an entry to all upper case."""

    def process(self, entry: str) -> List[str]:
        upper = entry.upper()
        if upper != entry:
            return [upper]
        else:
            return []

    def __str__(self):
        return "to_upper"    

TO_UPPER = ToUpper()   


class RemoveSpecialChars(AtomicRule):
    """ Removes all special chars; whitespace is not considered as a
        special char.
    """

    re_non_special_char = re.compile("[a-zA-Z0-9\s]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveSpecialChars.re_non_special_char.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return ["".join(entries)]
        else:
            return []

    def __str__(self):
        return "remove_sc"

REMOVE_SPECIAL_CHARS = RemoveSpecialChars()


class GetSpecialChars(AtomicRule):
    """Extracts the used special char (sequences)."""

    re_special_chars = re.compile("[^a-zA-Z0-9\s]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetSpecialChars.re_special_chars.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return entries
        else:
            return []

    def __str__(self):
        return "get_sc"

GET_SPECIAL_CHARS = GetSpecialChars()


class GetNumbers(AtomicRule):
    """ Extracts all numbers. """

    re_numbers = re.compile("[0-9]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetNumbers.re_numbers.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return entries
        else:
            return []

    def __str__(self):
        return "get_numbers"   

GET_NUMBERS = GetNumbers()


class RemoveNumbers(AtomicRule):
    """Removes all numbers from an entry."""

    re_no_numbers = re.compile("[^0-9]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveNumbers.re_no_numbers.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return ["".join(entries)]
        else:
            return []

    def __str__(self):
        return "remove_numbers"   

REMOVE_NUMBERS = RemoveNumbers()


class FoldWhitespace(AtomicRule):
    """ Folds all whitespace (spaces and tabs) to one space. """

    def process(self, entry: str) -> List[str]:
        last_entry = ""
        folded_entry = entry
        while folded_entry != last_entry:
            last_entry = folded_entry
            folded_entry = folded_entry\
                .replace("  "," ")\
                .replace("\t"," ") # May result in two or three subsequent spaces
        if entry != folded_entry:
            return [folded_entry]
        else:
            return []

    def __str__(self):
        return "fold_ws"

FOLD_WHITESPACE = FoldWhitespace()

rule_name: str,
class Capitalize(AtomicRule):
    """Capitalize a given entry."""

    def process(self, entry: str) -> List[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return []

    def __str__(self):
        return "capitalize"

CAPITALIZE = Capitalize()

class MangleDates(AtomicRule):
    """ Tries to identify numbers which are dates and then creates various
        representations for the respective date.
    """

    re_german_date = re.compile("[^0-9]*([0-9]{1,2})\.?([0-9]{1,2})\.?(19|20)?([0-9]{2})")

    def __init__(self): pass

    def process(self, entry: str) -> List[str]:
        r = MangleDates.re_german_date.match(entry)
        if not r:
            return []

        (d,m,c,y) = r.groups()
        """Currently we only accept dates between 1975 and 2025.
            The test ist not extremely precise, but should be acceptable for
            our purposes.
        """
        if int(d) > 31 or int(d) == 0 or int(m) > 12 or int(m) == 0 or (int(y) > 25 and int(y) < 75):
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
            else:
                mangled_dates.append("0"+d+m+y)
        else:
            if len(m) == 1:
                mangled_dates.append(d+"0"+m+y)
        return mangled_dates
            

    def __str__ (self):
        return "mangle_dates"

MANGLE_DATES = MangleDates()      


class Split(AtomicRule):
    """ Splits up an entry using the given split_char as a separator
        creating all sub splits.
    """

    def __init__(self, split_char : str):
        self.split_char = split_char
        return

    def process(self, entry: str) -> List[str]:
        segments = entry.split(self.split_char)
        segments_count = len(segments)
        if segments_count ==  1:
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
        return f"split {split_char_def}"            
  

class Replace(AtomicRule):
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

    def process(self, entry: str) -> List[str]: 
        e = entry       
        for k,v in self.replacement_table.items():
            # RECALL:   Replace maintains object identity if there is 
            #           nothing to replace.    
            e = e.replace(k,v) 
        if entry is e:
            # Filter entry if there was nothing to replace.
            return []
        else:
            return [e]
        
    def __str__(self):
        return f'replace "{self.replacements_filename}"'


class Discard(AtomicRule):
    """
    Discards the last term - recursively - of a string with multiple elements
    if the term is defined in the given file. The preceding 
    whitespace will also be discarded. For example, given the string:

        _Michael ist ein_

    and assuming that "ist" and "ein" should not be endings, the only
    string that will pass this rule would be "Michael".
    """

    def __init__(self, endings_filename):
        self.endings_filename = endings_filename

        endings : Set[str] = set()
        with open(locate_resource(endings_filename),"r",encoding="utf-8") as fin :
            for ending in fin:
                endings.add(ending.rstrip("\r\n"))       
        self.endings = endings

    def process(self, entry: str) -> List[str]: 
        all_terms = entry.split()
        if len(all_terms) == 1:
            return []
        count = 0
        while len(all_terms) > (-count + 1) and all_terms[count -1] in self.endings:
            count -= 1

        if count != 0 in self.endings:
            return [" ".join(all_terms[0:-count])]
        else:
            return []
        
    def __str__(self):
        return f'discard_endings"{self.endings_filename}"'


class Rule:
    """Representation of a complex rule.

    Instantiation of a complex rule which is made up of 
    multiple atomic transformations. An instance of Rule 
    basically just handles applying the atomic rules to 
    an entry and (potentially) every subsequently created entry.
    """

    def __init__(self, rules: List[AtomicRule]):
        self.rules = rules
        return

    def apply(self, entry):
        return apply_rules(entry,self.rules)

    def __str__(self) -> str:
        return " ".join(map(str,self.rules))


### PARSER SETUP AND CONFIGURATION


re_next_word = re.compile("^[^\s]+")
re_next_quoted_word = re.compile('^"[^"]+"')

def parse(rule) -> Callable[[str,str],Tuple[str,AtomicRule]]:
    """Generic parser for rules without parameters."""

    def parse_it(rule_name: str, rest_of_rule: str) -> Tuple[str, AtomicRule]:
        return (rest_of_rule,rule)

    return parse_it   


def parse_split(rule_name: str, rest_of_rule: str) -> Tuple[str, AtomicRule]:
    split_chars_match = re_next_word.match(rest_of_rule)
    raw_split_chars = split_chars_match.group(0)
    split_char = raw_split_chars \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    new_rest_of_rule = rest_of_rule[split_chars_match.end(0):].lstrip()
    return (new_rest_of_rule,Split(split_char))


def parse_replace(rule_name: str, rest_of_rule: str) -> Tuple[str, AtomicRule]:
    replace_filename_match = re_next_quoted_word.match(rest_of_rule)
    replace_filename = replace_filename_match.group(0).strip("\"")
    new_rest_of_rule = rest_of_rule[replace_filename_match.end(0):].lstrip()
    return (new_rest_of_rule,Replace(replace_filename))


def parse_discard_endings(rule_name: str, rest_of_rule: str) -> Tuple[str, AtomicRule]:
    endings_filename_match = re_next_quoted_word.match(rest_of_rule)
    if not endings_filename_match:
        raise Exception("discard_endings: file name missing (did you forgot the quotes(\")?)")
    endings_filename = endings_filename_match.group(0).strip("\"")
    new_rest_of_rule = rest_of_rule[endings_filename_match.end(0):].lstrip()    
    return (new_rest_of_rule,Discard(endings_filename))


macro_defs : Tuple[str,Rule] = { }

"""Mapping between the name of a rule and it's associated parameters parser."""
rule_parsers = {

    "report": parse(REPORT),
    
    # TRANSFORMERS
    "fold_ws": parse(FOLD_WHITESPACE),
    "to_lower": parse(TO_LOWER),
    "to_upper": parse(TO_UPPER),
    "get_numbers": parse(GET_NUMBERS),
    "remove_numbers": parse(REMOVE_NUMBERS),
    "remove_ws": parse(REMOVE_WHITESPACE),
    "remove_sc": parse(REMOVE_SPECIAL_CHARS),
    "get_sc": parse(GET_SPECIAL_CHARS),
    "capitalize" : parse(CAPITALIZE),
    "deleetify" : parse(DELEETIFY),
    "strip" : parse(STRIP),
    "mangle_dates" : parse(MANGLE_DATES),

    "split": parse_split,
    "replace" : parse_replace,
    "discard_endings" : parse_discard_endings,
}


def parse_rest_of_rule(previous_rules : List[AtomicRule], line_number, rest_of_rule : str) -> Tuple[str, AtomicRule]:
    # Get name of rule parser
    next_rule_parser_match = re_next_word.match(rest_of_rule)
    next_rule_parser_name = next_rule_parser_match.group(0)

    # Check for rule modifiers
    keep_always = (next_rule_parser_name[0] == "+")                
    keep_if_filtered = (next_rule_parser_name[0] == "*") 
    if keep_always or keep_if_filtered:
        next_rule_parser_name = next_rule_parser_name[1:]

    result : Tuple[str, AtomicRule] = None
    next_rule_parser = rule_parsers.get(next_rule_parser_name)
    if next_rule_parser is not None:
        new_rest_of_rule = rest_of_rule[next_rule_parser_match.end(
            0):].lstrip()
        result = next_rule_parser(next_rule_parser_name, new_rest_of_rule)
    elif macro_defs.get(next_rule_parser_name) is not None:
        macro_def = macro_defs.get(next_rule_parser_name)
        new_rest_of_rule = rest_of_rule[next_rule_parser_match.end(
            0):].lstrip()
        result = (
            new_rest_of_rule,
            Macro(next_rule_parser_name,macro_def.rules)
        )
    else:
        print(
            f"[error][{line_number}] unknown command: {next_rule_parser_name}", 
            file=sys.stderr
        )
        return None        

    if keep_always:
        (new_rest_of_rule,base_rule) = result
        result = (new_rest_of_rule,KeepAlwaysModifier(base_rule))
    if keep_if_filtered:
        (new_rest_of_rule,base_rule) = result
        result = (new_rest_of_rule,KeepOnlyIfFilteredModifier(base_rule))
        return result
    


def parse_rule(line_number:int, is_def : bool, sline:str):
    # Parse a single rule definition in collaboration with the
    # respective atomic parsers.
    atomic_rules: List[AtomicRule] = []
    while len(sline) > 0:
        parsed_atomic_rule = parse_rest_of_rule(atomic_rules, line_number, sline)
        if parsed_atomic_rule:
            (sline, atomic_rule) = parsed_atomic_rule
            atomic_rules.append(atomic_rule)
            if  not is_def and\
                len(sline) == 0 and\
                not (
                    isinstance(atomic_rule,Report) 
                    or 
                    (isinstance(atomic_rule,Macro) and isinstance(atomic_rule.rules[-1],Report))
                ):
                print(
                    f"[info][{line_number}] adding report as the last rule", 
                    file=sys.stderr
                )
                atomic_rules.append(Report())
        else:
            # If the parsing of an atomic rule fails, we just
            # ignore the line as a whole.
            atomic_rules = None
            break

    return Rule(atomic_rules)


def parse_rules(rules_filename : str, verbose : bool) -> List[Rule]:
    """Parses the rule definitions together with the atomic rule parsers. 

    The split between the generic parser and the atomic rule parsers 
    is as follows:
    This method parses the next word to determine the next atomic rule;
    the atomic rule is then responsible for parsing its parameters and
    removing them from the string.
    """

    rules: List[Rule] = []

    abs_filename = locate_resource(rules_filename)
    with open(abs_filename, 'r', encoding='utf-8') as rules_file:
        line_number = 0
        for rule_def in rules_file.readlines():
            line_number = line_number + 1
            sline = rule_def.strip()

            # ignore comments and empty lines
            if sline.startswith('#') or len(sline) == 0:
                continue

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

            elif sline.startswith("def"):
                macro_def = sline[len("def")+1:]
                macro_name_match = re_next_word.match(macro_def)
                macro_name = macro_name_match.group(0)
                macro_body = macro_def[macro_name_match.end(0):].lstrip()
                if macro_name.upper() != macro_name:
                    raise Exception(f"macro names need to be upper case: {macro_name}")
                rule = parse_rule(line_number, True, macro_body)
                if rule:
                    macro_defs[macro_name] = rule

            else:
                rule = parse_rule(line_number, False, sline)
                if rule:
                    rules.append(rule)

    return rules


def transform_entries(dict_filename: str, verbose : bool, rules: List[Rule]):
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
            reported_entries.clear()
            for r in rules:
                if verbose:
                    escaped_sentry = sentry\
                        .replace("\\","\\\\")\
                        .replace("\"","\\\"")
                    print(
                        f'[{count}:"{escaped_sentry}"] applying rule: {r}',
                        file=sys.stderr
                    )            
                r.apply(sentry)            


def main() -> int:
    parser = argparse.ArgumentParser(
        description=
        """Generates an attack dictionary based on a plain dictionary.

        """
    )
    parser.add_argument(
        '-r', 
        '--rules', 
        help="a .td file with the rules that will be applied to the dictionary entries", 
        default="default_rules.td"
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

    all_rules = parse_rules(args.rules, args.verbose)
    
    transform_entries(args.dictionary, args.verbose, all_rules)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
