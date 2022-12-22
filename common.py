import os
from sys import stderr
from datetime import datetime
import importlib

import pynuspell

class IllegalStateError(RuntimeError): 
    pass

class InitializationFailed(RuntimeError):
    """ Errors that are related to user problems. """
    pass

def escape(s : str) -> str:
    return \
        s.replace('\\',"\\\\")\
         .replace('\n',"\\n")\
         .replace('\t',"\\t")\
         .replace('\r',"\\r")\
         .replace('\"',"\\\"")

def unescape(s : str) -> str:
    """ The escape character is \ and the following escape 
        sequences are supported:
        \\  => \
        \n  => <newline>
        \t  => <tab>
        \r  => <carriage return>
        \"  => "

        This method is not optimized and should not used to
        process entries!
    """
    return \
        s.replace("\\\\",'\\')\
         .replace("\\n",'\n')\
         .replace("\\t",'\t')\
         .replace("\\r",'\r')\
         .replace("\\\"",'"')\

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
        common_path = os.path.dirname(__file__)
        dj_filename = os.path.join(common_path,filename)
        resources_filename = os.path.join(common_path,"resources",filename)
        if os.path.exists(dj_filename):
            return dj_filename
        elif os.path.exists(resources_filename):
            return resources_filename
        else:
            error = f"neither ./{filename} nor {dj_filename} nor {resources_filename} exists"
            raise FileNotFoundError(error)
    except Exception as e:
        raise InitializationFailed(f"can't locate {filename}: {e}")

def read_utf8file(filename: str) -> list[str] :
    abs_filename = locate_resource(filename)
    lines = []
    try: 
        with open(abs_filename, 'r', encoding='utf-8') as fin:
            for line in fin:
                # We want to be able to strip words with spaces
                # at the beginning or end.
                stripped_line = line.rstrip("\r\n")
                if len(stripped_line) > 0:
                    lines.append(stripped_line)
    except Exception as e:
        raise InitializationFailed(f"can't read {filename}: {e}")
    return lines

def enrich_filename(filename: str) -> str:
    """ Extends the current filename with the current date.
    """
    date = datetime.today().strftime('%Y_%m_%d')
    if filename.find(date) >= 0:
        return filename

    last_dot_index = filename.rfind(".")    
    if last_dot_index == -1:
        return filename+"."+date
    
    return filename[0:last_dot_index]+"."+date+filename[last_dot_index:]

def get_filename(filename : str) -> str:
    if filename[0] != "\"" or filename[len(filename)-1] != "\"":
        raise Exception("the filename has to be quoted (\")")
    return filename[1:-1]

""" Hunspell
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
"""

def _load_dict(lang : str):
    try:
        last_folder_seperator = lang.rfind("/")
        lang_path = lang[0:last_folder_seperator]        
        abs_lang = os.path.join(locate_resource(lang_path),lang[last_folder_seperator+1:])
        return pynuspell.load_from_path(abs_lang)
    except Exception as e:
        raise ValueError("can't load: "+lang+"; "+str(e))

dictionaries = {
    "en":_load_dict("dicts/en/en_US"),            # American English
    "de":_load_dict("dicts/de/de_DE_frami"),      # German (Modern)
    "nl":_load_dict('dicts/nl_NL/nl_NL'),         # Netherlands
}
"""
    "da":_load_dict('dicts/da_DK/da_DK'),         # Danish
    "pl":_load_dict('dicts/pl_PL/pl_PL'),         # Polish
    "fr":_load_dict('dicts/fr_FR/fr'),            # French
    "ro":_load_dict('dicts/ro/ro_RO'),            # Romanian
    "sr":_load_dict('dicts/sr/sr'),               # Serbian
    "sl":_load_dict('dicts/sl_SI/sl_SI'),         # Slovenian
    "sq":_load_dict('dicts/sq_AL/sq_AL'),         # Albanian
    "bs":_load_dict('dicts/bs_BA/bs_BA'),         # Bosnian
    "bg":_load_dict('dicts/bg_BG/bg_BG'),         # Bulgarian
    "hr":_load_dict('dicts/hr_HR/hr_HR'),         # Croatian
    "hu":_load_dict('dicts/hu_HU/hu_HU'),         # Hungarian
    "it":_load_dict('dicts/it_IT/it_IT'),         # Italian
    "pt":_load_dict('dicts/pt_PT/pt_PT'),         # Portugese
    "es":_load_dict('dicts/es/es_ES')             # Spanish (Spain)
"""


_nlp_models = {
    # The initial value object (string) will be replaced 
    # by the GENSIM model when the model was loaded by
    # a call to the `get_nlp_model` method.
    "twitter" : 'glove-twitter-200',        
    "google"  : 'word2vec-google-news-300',
    "wiki"    : 'glove-wiki-gigaword-300'
}

def get_nlp_model(model : str):
    global _nlp_models
    nlp_model = _nlp_models[model]
    if isinstance(nlp_model,str):
        gensim_module = importlib.import_module("gensim.downloader")
        gensim_load = getattr(gensim_module,"load")
        print(f"[info] loading {model} (this will take time)", file=stderr)
        nlp_model = gensim_load(nlp_model)
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
