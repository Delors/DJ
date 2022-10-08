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
  
    def test_arbitrary_chars(self):       
        suggestions = CS.process("MwDkadfuaSSeeeadfas")
        self.assertIsNone(suggestions)