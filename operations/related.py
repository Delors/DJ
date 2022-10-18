from typing import List
from contextlib import suppress

from operations.operation import Operation
from common import get_nlp_model


class Related(Operation):
    """ Returns those terms that are most related; i.e. surpass the 
        RELATEDNESS factor.

        In general, we first search the most related terms in the 
        individual nlp models and only after that create a merged 
        list. After that we take the (at most 5) most related terms across 
        all models. 
    """

    
    MAX_RELATED = 5
    TOPN = 10
    assert MAX_RELATED <= TOPN

    def __init__(self,MIN_RELATEDNESS : float = 0.6):
        self._twitter = None
        # self._google = None
        self._wiki = None
        self.MIN_RELATEDNESS = MIN_RELATEDNESS
        self.KEEP_ALL_RELATEDNESS = min(MIN_RELATEDNESS + 0.15, 1.0)
        return

    def is_transformer(self) -> bool: 
        return True
        
    def process(self, entry: str) -> List[str]:
        if not self._twitter: 
            self._twitter = get_nlp_model("twitter")
        get_tms = self._twitter.most_similar

        # if not self._google: 
        #    self._google = get_nlp_model("google")
        # get_gms = self._google.most_similar

        if not self._wiki: 
            self._wiki = get_nlp_model("wiki")                
        get_wms = self._wiki.most_similar

        lentry = entry.lower()        
        ms = []        

        # recall that the twitter model only uses small letters
        with suppress(KeyError): ms = get_tms(topn=self.TOPN,positive=[lentry]) 

        #with suppress(KeyError): ms.extend(get_gms(topn=TOPN,positive=[entry])) 
        
        # recall that the wiki model only uses small letters
        with suppress(KeyError): ms.extend(get_wms(topn=self.TOPN,positive=[lentry]))


        ms.sort(key = lambda e : e[1], reverse = True)
        result = set()
        for (k,v) in ms:
            if v >= self.KEEP_ALL_RELATEDNESS:
                result.add(k)
            elif v >= self.MIN_RELATEDNESS:
                if len(result) >= self.MAX_RELATED:
                    break
                else:
                    result.add(k)
            else:
                break

        return  list(result)

    def __str__(self):
        return f"related {self.MIN_RELATEDNESS}"
