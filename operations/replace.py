from typing import List

from operations.operation import Transformer
from common import locate_resource


class Replace(Transformer):
    """ Replaces a character by another character.

        (If you want to replace a single character by multiple other 
        characters use the "map" operation.)
    """

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
                    raise SyntaxError(f"the key ({key}) is already used")                   
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
            return None
        else:
            return [e]
        
    def __str__(self):
        return f'replace "{self.replacements_filename}"'
