from dj_ops import PerEntryExtractor


class Detriplicate(PerEntryExtractor):
    """
    Transforms entries where the second and third thirds are a 
    repetition of the first third.

    E.g. "TestTestTest" will be transformed to "Test".
    """

    def op_name() -> str: return "detriplicate"

    def process(self, entry: str) -> list[str]:
        length = len(entry)
        if length % 3 != 0:
            return None
        frag_length = length//3
        first_third = entry[0:frag_length]
        second_third = entry[frag_length:2*frag_length]
        third_third = entry[-frag_length:]
        if first_third == second_third and second_third == third_third:
            return [first_third]
        else:
            return None
        
    def derive_rules(self, entry: str) -> list[tuple[str,str]]:
        # Returned value: the first string is the result of the 
        #                 operation; the second is the operation
        #                 to regenerate the original string.
        r = self.process(entry)
        if r is not None:
            return [(r[0],"multiply 3")]
                
        return r
    


DETRIPLICATE = Detriplicate()
