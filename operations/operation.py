from abc import ABC, abstractmethod
from typing import List

class Operation(ABC):
    """ Representation of an operation. An operation processes an entry
        and produces zero (`[]`) to many entries. An operation which 
        does not apply to an entry returns `None`. For a precise definition
        of "does not apply" see the documentation of the respective 
        classes of operations.

        An operation is either:
        - a transformation which takes an entry and returns None or between
          zero and many new entries; i.e., the original entry will
          never be returned. If a transformation does not generate
          new entries, the transformation is considered to be not
          applicable to the entry and None is returned.
          For example, if an entry only consists of special characters
          and the operation removes all special characters, a empty 
          list (not None) will be returned. But, if the entry contains
          no special characters and, therefore, nothing would be removed
          None would be returned.
        - an extractor which extracts one to multiple parts of an entry. 
          An extractor might "extract" the original entry. For example,
          an extractor for numbers might return the original entry if 
          the entry just consists of numbers.
          An extractor which does not extract a single entry is not
          considered to be applicable and None is returned.
        - a meta operation which manipulates the behavior of an
          extractor or a transformation.
        - a filter operation which takes an entry and either returns
          the entry (`[entry]`) or the empty list (`[]`). Hence, a filter
          is considered to be always applicable.
        - a report operation which either collects some statistics or
          which prints out an entry but always just returns the entry
          as is.
        - a macro which combines one to many operations and which basically
          provides a convenience method to facilitate the definition of
          a set of operations which should be carried out in a specific order
          and which may be used multiple times.
    """

    @abstractmethod
    def process(self, entry: str) -> List[str]:
        """
        Processes the given entry and returns the list of new entries.
        If an operation applies, i.e., the operation has some effect, 
        a list of new entries (possibly empty) will be returned.
        If an operation does not apply at all, None should be returned.
        Each operation has to clearly define when it applies and when not.

        For example, an operation to remove special chars would apply to
        an entry consisting only of special chars and would return
        the empty list in that case. If, however, the entry does not 
        contain any special characters, None would be returned.

        E.g., an operation that just extracts certain characters or which 
        replaces certain characters will always either return a 
        non-empty list (`[]`) or `None` (didn't apply).
        """
        pass

    
    def close(self):           
        """
        Close is called after all entries of the dictionary have been
        processed and all operations have been executed.
        """
        pass

    def is_transformer(self) -> bool: return False

    def is_extractor(self) -> bool: return False    

    def is_meta_op(self) -> bool: return False

    def is_macro(self) -> bool: return False

    def is_reporter(self) -> bool: return False        

    def is_filter(self) -> bool: return False 