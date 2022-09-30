from typing import List

from operations.operation import Operation
from common import get_nlp_model


class Related(Operation):
    
    def __init__(self):
        self._twitter = None
        self._google = None
        return

    def is_transformer(self) -> bool: return True
        
    def process(self, entry: str) -> List[str]:
        if not self._twitter: 
            self._twitter = get_nlp_model("twitter")
        if not self._google: 
            self._google = get_nlp_model("google")
        try:
            return list(
                t for (t,_) in self._twitter.most_similar(topn=3,positive=[entry]) 
            )
        except:
            return []
        
    def __str__(self):
        return "related"

RELATED = Related()