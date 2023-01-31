from math import isnan
from typing import List
from contextlib import suppress

from dj_ast import Transformer, TDUnit, ASTNode
from common import InitializationFailed, get_nlp_model


class Related(Transformer):
    """ Returns those terms that are most related; i.e. surpass the 
        RELATEDNESS factor.

        In general, we first search the most related terms in the 
        individual nlp models and only after that create a merged 
        list. After that we take the (at most 5) most related terms across 
        all models. 
    """

    def op_name() -> str: return "related"

    K = 5
    KEEP_ALL_RELATEDNESS = 0.75

    def __init__(self, MIN_RELATEDNESS: float = 0.6):
        self._twitter = None
        # self._google = None
        self._wiki = None
        self.MIN_RELATEDNESS = MIN_RELATEDNESS

    def init(self, td_unit: 'TDUnit', parent: 'ASTNode', verbose: bool):
        super().init(td_unit, parent, verbose)
        # The test is required here, because both variables are user
        # configurable.
        if self.KEEP_ALL_RELATEDNESS < self.MIN_RELATEDNESS:
            raise InitializationFailed(
                f"KEEP_ALL_RELATEDNESS {self.KEEP_ALL_RELATEDNESS} has to be " +
                f"larger than the MIN_RELATEDNESS {self.MIN_RELATEDNESS}"
            )
        if self.MIN_RELATEDNESS <= 0 or self.MIN_RELATEDNESS >= 1.0:
            raise InitializationFailed(
                f"MIN_RELATEDNESS {self.MIN_RELATEDNESS} has to be in range (0,1.0)"
            )

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
        with suppress(KeyError):
            ms = get_tms(topn=self.K*2, positive=[lentry])

        # with suppress(KeyError): ms.extend(get_gms(topn=self.K,positive=[entry]))

        # recall that the wiki model only uses small letters
        with suppress(KeyError):
            ms.extend(get_wms(topn=self.K*2, positive=[lentry]))

        ms.sort(key=lambda e: e[1], reverse=True)
        result = set()
        for (k, v) in ms:
            if v >= self.KEEP_ALL_RELATEDNESS:
                result.add(k)
            elif v >= self.MIN_RELATEDNESS:
                if len(result) >= self.K:
                    break
                else:
                    result.add(k)
            else:
                break

        return list(result)

    def __str__(self):
        return f"{Related.op_name()} {self.MIN_RELATEDNESS}"
