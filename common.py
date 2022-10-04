import os
import sys
from sys import stderr
from abc import ABC
from typing import List, Set, Tuple, Callable

import hunspell
import gensim.downloader as gensim

from operations.operation import Operation

class IllegalStateError(RuntimeError):
    pass

def escape(s : str) -> str:
    return \
        s.replace('\\',"\\\\")\
         .replace(' ',"\\s")\
         .replace('\t',"\\t")\

def unescape(s : str) -> str:
    return \
        s.replace("\\\\",'\\')\
         .replace("\\s",' ')\
         .replace("\\t",'\t')\

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

def get_filename(filename : str) -> str:
    if filename[0] != "\"" or filename[len(filename)-1] != "\"":
        raise Exception("the filename has to be quoted (\")")
    return filename[1:-1]


def _load_dict(lang : str):
    try:
        dic = 'dicts/'+lang+'.dic'
        aff = 'dicts/'+lang+'.dic'
        return hunspell.HunSpell(dic,aff)
    except Exception as e:
        raise ValueError("can't load: "+dic+"; "+str(e))

dictionaries = {
    "en":_load_dict("en/en_US"),            # American English
    "de":_load_dict("de/de_DE_frami"),      # German (Modern)
    "nl":_load_dict('nl_NL/nl_NL'),         # Netherlands
    "da":_load_dict('da_DK/da_DK'),         # Danish
    "pl":_load_dict('pl_PL/pl_PL'),         # Polish
    "fr":_load_dict('fr_FR/fr'),            # French
    "ro":_load_dict('ro/ro_RO'),            # Romanian
    "sr":_load_dict('sr/sr'),               # Serbian
    "sl":_load_dict('sl_SI/sl_SI'),         # Slovenian
    "sq":_load_dict('sq_AL/sq_AL'),         # Albanian
    "bs":_load_dict('bs_BA/bs_BA'),         # Bosnian
    "bg":_load_dict('bg_BG/bg_BG'),         # Bulgarian
    "hr":_load_dict('hr_HR/hr_HR'),         # Croatian
    "hu":_load_dict('hu_HU/hu_HU'),         # Hungarian
    "it":_load_dict('it_IT/it_IT'),         # Italian
    "pt":_load_dict('pt_PT/pt_PT'),         # Portugese
    "es":_load_dict('es/es_ES')             # Spanish (Spain)
}


_nlp_models = {
    # the value object (string) will be replaced 
    # by the GENSIM model when the model was loaded
    "twitter" : 'glove-twitter-200',        
    "google"  : 'word2vec-google-news-300',
    "wiki"    : 'glove-wiki-gigaword-300'
}

def get_nlp_model(model : str):
    global _nlp_models
    nlp_model = _nlp_models[model]
    if isinstance(model,str):
        print(f"[info] loading {model} (this will take time)", file=stderr)
        nlp_model = gensim.load(nlp_model)
        _nlp_models[model] = nlp_model
        print(f"[info] loaded {model}({nlp_model})", file=stderr)
    return nlp_model


_nlp_vocabs = {
    # EMPTY! - lazily initialized by calling "get_nlp_vocab"
}

def get_nlp_vocab(model: str) :
    # Returns an nlp model's underlying dictionary. This can, e.g., 
    # be used to check if a word exists in the model.
    global _nlp_vocabs
    nlp_vocab = _nlp_vocabs.get(model)
    if not nlp_vocab:
        print(
            f"[info] initializing {model} vocabulary (this will take time)",
            file=stderr
        )
        nlp_vocab = get_nlp_model(model).key_to_index
        _nlp_vocabs[model] = nlp_vocab
        print(f"[info] initialized {model} vocabulary", file=stderr)
    return nlp_vocab
