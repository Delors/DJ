import unittest

from operations.correct_spelling import CORRECT_SPELLING as CS

class TestCorrectSpelling(unittest.TestCase):


    def test_is_transformer(self):
        self.assertTrue(CS.is_transformer())

    def test__str__(self):
        self.assertEqual(CS.__str__(),"correct_spelling")

    def test_correct_word(self):       
        self.assertEqual(CS.process("ape"),[])

    def test_wrong_capitalization(self):       
        self.assertEqual(CS.process("munich"),["Munich"])        
         
    def test_multiple_corrections(self):       
        suggestions = CS.process("Houres")
        self.assertIn("Hours", suggestions)
        self.assertIn("Houses", suggestions)
  
    def test_use_of_damerau_levenshtein_is_default(self):
        self.assertTrue(CS.USE_DAMERAU_LEVENSHTEIN)

    def test_use_of_damerau_levenshtein_corrections(self):       
        suggestions = CS.process("Tset")
        self.assertIn("Test", suggestions)

    def test_handling_of_capitalization(self):       
        suggestions = CS.process("TeSt")
        self.assertListEqual(["Test"], suggestions)

        suggestions = CS.process("hallenbad")
        self.assertListEqual(["Hallenbad"], suggestions)     
        
        suggestions = CS.process("HaLlenBad")
        self.assertListEqual(["Hallenbad"], suggestions)        

    def test_arbitrary_chars(self):       
        suggestions = CS.process("MwDkadfuaSSeeeadfas")
        self.assertIsNone(suggestions)

    ### We change the distance calculator to Levenshtein:

    def test_use_of_levenshtein_corrections(self):       
        CS.USE_DAMERAU_LEVENSHTEIN = False
        suggestions = CS.process("Tset")
        self.assertNotIn("Test", suggestions)