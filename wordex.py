#!/usr/bin/python3


# Script to identify words in dictionaries

from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable
import sys

import re

import hunspell
from Levenshtein import distance

match_words = re.compile("[^\W\d_]+")

def _load_dict(lang : str):
    try:
        dic = 'dicts/'+lang+'.dic'
        aff = 'dicts/'+lang+'.dic'
        return hunspell.HunSpell(dic,aff)
    except Exception as e:
        raise ValueError("can't load: "+dic+"; "+str(e))

languages = {
    "en":_load_dict("en/en_US"),
    "de":_load_dict("de/de_DE_frami"),
    "nl":_load_dict('nl_NL/nl_NL'),
    "fr":_load_dict('fr_FR/fr')
}

def base_strip(entry : str) -> str:
    """Takes a string and removes all digits and special chars 
       at the beginning and end of the string."""

    # 0. strip CR/LF
    entry = entry.strip()
    # 1. strip numbers at the start/end
    s = entry.strip("0123456789")
    # 2. strip special chars at the start/end
    s = s.strip("!§$%&/(){[]}=?*+~'#-_.:,;|<>")
    if s != entry:
        return base_strip(s)
    else:
        return entry

def identify_words(entry : str) -> List[str]:
    # 1. let's check if the word is a known word.
    if any(d.spell(entry) for d in languages.values()):
        return [entry]

    # 2. let's check if the word is misspelled.
    # Here, we only consider misspellings with a 
    # maximum levenshtein distance of one and
    # only if the result is a "complete" word. 
    # Eg. given "Computers" its potential
    # correction "Computer s" is ignored.
    words = []
    for d in languages.values():
        for c in d.suggest(entry):
            if distance(entry,c) == 1 and c.find(" ") == -1:
                words.append(c)
    return words


d_in = sys.stdin
for entry in d_in:
    # let's do some preprocessing:
    base_entry = base_strip(entry)

    # let's check if the word is a regular word
    candidates = identify_words(base_entry)
    if len(candidates) > 0:
        for w in candidates:
            print(w)
        continue    

    # Let's try some splitting along special chars and digits to identify
    # sentences, such as:
    #   Dies_ist_ein_Test
    #   Ich.liebe.Dich
    candidates = match_words.findall(base_entry)
    if len(candidates) > 1:
        non_words = []
        for candidate in candidates:
            words = identify_words(candidate) 
            if len(words) == 0:
                non_words.append(candidate)
            else:
                for w in words: print(w)
        if len(non_words) == 0:            
            continue

        print("non-words: ",non_words)


            
