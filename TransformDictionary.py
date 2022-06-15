#!/usr/bin/python3

# Bundeskriminalamt KT53
# Dr. Michael Eichberg (michael.eichberg@bka.bund.de)
# 2022

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

import sys
import argparse
from spellchecker import SpellChecker

import re

"""The global list of all entries which will always be ignored."""
ignored_entries = set()


def apply_rules(entry : str, rules) -> List[str]:
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


""" The set of reported entries per entry. This list is cleared
    by the transform_entries method.
"""
reported_entries : Set[str] = set()

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
    transformation. The only exception is the KeepEntryModifier which
    acts like a modifier ("+" directly before the rule name) 
    and is implemented as a wrapper.    
    """

    @abstractmethod
    def process(self, entry: str) -> List[str]:
        pass


class Report(AtomicRule):
    """The "report" rule prints out the entry. 

    Prints out the current state of the transformation of an entry.
    Can also be used if an intermediate result is actually a desired 
    output and we do not want to have multiple rules. For example:

    ___remove_ws +report replace "UmlautToAscii" report___
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
    """The input entry will also be an output entry."""

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
    """The input entry will be an output entry if the wrapped rule
        completely rejects the entry.
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

    spell_en = SpellChecker(language="en")
    spell_de = SpellChecker(language="de")

    def process(self, entry: str) -> List[str]:
        deleetified_entry = entry.replace("3","e").replace("4","a")
        if entry == deleetified_entry:
            # There is no leet speak...
            return []
        deleetified_terms = deleetified_entry.split()
        known_en = DeLeetify.spell_en.known 
        known_de = DeLeetify.spell_de.known 
        if  len(known_en(deleetified_terms)) == len(deleetified_terms)\
            or\
            all(len(known_de(t)) != 0 for t in deleetified_terms):
            return [deleetified_entry]
        else:
            return []

    def __str__(self):
        return "deleetify"

DELEETIFY = DeLeetify()   


class RemoveWhitespace(AtomicRule):

    def process(self, entry: str) -> List[str]:
        split_entries = entry.split()
        if len(split_entries) == 1:  
            return []
        else:
            return ["".join(split_entries)]

    def __str__(self):
        return "remove_ws"

REMOVE_WHITESPACE = RemoveWhitespace()        


class ToLower(AtomicRule):

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

    non_special_char_pattern = re.compile("[a-zA-Z0-9\s]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveSpecialChars.non_special_char_pattern.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return ["".join(entries)]
        else:
            return []

    def __str__(self):
        return "remove_sc"

REMOVE_SPECIAL_CHARS = RemoveSpecialChars()


class GetNumbers(AtomicRule):

    numbers_pattern = re.compile("[0-9]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in GetNumbers.numbers_pattern.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return entries
        else:
            return []

    def __str__(self):
        return "get_numbers"   

GET_NUMBERS = GetNumbers()


class RemoveNumbers(AtomicRule):

    no_numbers_pattern = re.compile("[^0-9]+")

    def process(self, entry: str) -> List[str]:
        entries = [
            i.group(0) 
            for i in RemoveNumbers.no_numbers_pattern.finditer(entry)
        ]
        if len(entries) >= 1 and entry != entries[0]:
            return ["".join(entries)]
        else:
            return []

    def __str__(self):
        return "remove_numbers"   

REMOVE_NUMBERS = RemoveNumbers()


class FoldWhitespace(AtomicRule):

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


class Capitalize(AtomicRule):

    def process(self, entry: str) -> List[str]:
        capitalized = entry.capitalize()
        if entry != capitalized:
            return [capitalized]
        else:
            return []

    def __str__(self):
        return "capitalize"

CAPITALIZE = Capitalize()


class Split(AtomicRule):

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
        
        replacement_table : dict[str,str] = {}
        with open(replacements_filename,"r", encoding='utf-8') as replace_file :
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
    Discards the last term of a string with multiple elements
    if the term is defined in the given file. The preceeding 
    whitespace will also be discarded.
    """

    def __init__(self, endings_filename):
        self.endings_filename = endings_filename

        endings : Set[str] = set()
        with open(endings_filename,"r",encoding="utf-8") as fin :
            for ending in fin:
                endings.add(ending.rstrip("\r\n"))       
        self.endings = endings

    def process(self, entry: str) -> List[str]: 
        all_terms = entry.split()
        if len(all_terms) == 1:
            return []
        if all_terms[-1] in self.endings:
            return [" ".join(all_terms[0:-1])]
        else:
            return []
        
    def __str__(self):
        return f'discard "{self.endings_filename}"'


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


next_word_pattern = re.compile("^[^\s]+")
next_quoted_word_pattern = re.compile('^"[^"]+"')

def parse(rule) -> Callable[[str],Tuple[str,AtomicRule]]:
    """Generic parser for rules without parameters."""

    def parse_it(rest_of_rule: str) -> Tuple[str, AtomicRule]:
        return (rest_of_rule,rule)

    return parse_it   


def parse_split(rest_of_rule: str) -> Tuple[str, AtomicRule]:
    split_chars_match = next_word_pattern.match(rest_of_rule)
    raw_split_chars = split_chars_match.group(0)
    split_char = raw_split_chars \
            .replace("\\t","\t") \
            .replace("\\s"," ") \
            .replace("\\\\","\\")
    new_rest_of_rule = rest_of_rule[split_chars_match.end(0):].lstrip()
    return (new_rest_of_rule,Split(split_char))


def parse_replace(rest_of_rule: str) -> Tuple[str, AtomicRule]:
    replace_filename_match = next_quoted_word_pattern.match(rest_of_rule)
    replace_filename = replace_filename_match.group(0).strip("\"")
    new_rest_of_rule = rest_of_rule[replace_filename_match.end(0):].lstrip()
    return (new_rest_of_rule,Replace(replace_filename))


def parse_discard_endings(rest_of_rule: str) -> Tuple[str, AtomicRule]:
    endings_filename_match = next_quoted_word_pattern.match(rest_of_rule)
    if not endings_filename_match:
        raise Exception("discard_endings: file name missing (did you forgot the quotes(\")?)")
    endings_filename = endings_filename_match.group(0).strip("\"")
    new_rest_of_rule = rest_of_rule[endings_filename_match.end(0):].lstrip()
    return (new_rest_of_rule,Discard(endings_filename))


custom_rules : Tuple[str,Rule] = { }

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
    "capitalize" : parse(CAPITALIZE),
    "deleetify" : parse(DELEETIFY),

    "split": parse_split,
    "replace" : parse_replace,
    "discard_endings" : parse_discard_endings,
}


def parse_rest_of_rule(previous_rules : List[AtomicRule], line_number, rest_of_rule : str) -> Tuple[str, AtomicRule]:
    # Get name of rule parser
    next_rule_parser_match = next_word_pattern.match(rest_of_rule)
    next_rule_parser_name = next_rule_parser_match.group(0)

    # Check for rule modifiers
    keep_always = (next_rule_parser_name[0] == "+")                
    keep_if_filtered = (next_rule_parser_name[0] == "*") 
    if keep_always or keep_if_filtered:
        next_rule_parser_name = next_rule_parser_name[1:]

    result :  Tuple[str, AtomicRule] = None
    next_rule_parser = rule_parsers.get(next_rule_parser_name)
    if next_rule_parser is not None:
        new_rest_of_rule = rest_of_rule[next_rule_parser_match.end(
            0):].lstrip()
        result = next_rule_parser(new_rest_of_rule)
    elif custom_rules.get(next_rule_parser_name) is not None:
        custom_rule_instance = custom_rules.get(next_rule_parser_name)
        new_rest_of_rule = rest_of_rule[next_rule_parser_match.end(
            0):].lstrip()
        result = (
            new_rest_of_rule,
            Macro(next_rule_parser_name,custom_rule_instance.rules)
        )

    if keep_always:
        (new_rest_of_rule,base_rule) = result
        result = (new_rest_of_rule,KeepAlwaysModifier(base_rule))
    if keep_if_filtered:
        (new_rest_of_rule,base_rule) = result
        result = (new_rest_of_rule,KeepOnlyIfFilteredModifier(base_rule))

    if result is not None:
        return result
    
    print(
        f"[error][{line_number}] unknown command: {next_rule_parser_name}", 
        file=sys.stderr
    )
    return None


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

    with open(rules_filename, 'r', encoding='utf-8') as rules_file:
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

                with open(filename[1:-1],"r", encoding='utf-8') as fin:
                    for ignore_entry in fin:
                        # We want to be able to strip words with spaces
                        # at the beginning or end.
                        stripped_ignore_entry = ignore_entry.rstrip("\r\n")
                        if len(stripped_ignore_entry) > 0:
                            ignored_entries.add(stripped_ignore_entry)

            elif sline.startswith("def"):
                custom_rule_def = sline[len("def")+1:]
                rule_name_match = next_word_pattern.match(custom_rule_def)
                rule_name = rule_name_match.group(0)
                rule_body = custom_rule_def[rule_name_match.end(0):].lstrip()
                if rule_name.upper() != rule_name:
                    raise Exception(f"custom rules need to be upper case: {rule_name}")
                rule = parse_rule(line_number, True, rule_body)
                if rule:
                    custom_rules[rule_name] = rule

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
        required=True
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
