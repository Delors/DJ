import unittest

from operations.correct_spelling import CorrectSpelling


class TestCorrectSpelling(unittest.TestCase):

    def setUp(self):
        self.CS = CorrectSpelling().init(None,None)

    def test_is_transformer(self):        
        self.assertTrue(self.CS.is_transformer())

    def test__str__(self):
        self.assertEqual(self.CS.__str__(), "correct_spelling")

    def test_correct_word(self):
        self.assertEqual(self.CS.process("ape"), [])

    def test_wrong_capitalization(self):
        self.assertEqual(self.CS.process("munich"), ["Munich"])

    def test_multiple_corrections(self):
        suggestions = self.CS.process("Houres")
        self.assertIn("Hours", suggestions)
        self.assertIn("Houses", suggestions)

    def test_use_of_damerau_levenshtein_is_default(self):
        self.assertTrue(self.CS.USE_DAMERAU_LEVENSHTEIN)

    def test_use_of_damerau_levenshtein_corrections(self):
        suggestions = self.CS.process("Tset")
        self.assertIn("Test", suggestions)

    def test_handling_of_capitalization(self):
        suggestions = self.CS.process("TeSt")
        self.assertListEqual(["Test"], suggestions)

        suggestions = self.CS.process("hallenbad")
        self.assertListEqual(["Hallenbad"], suggestions)

        suggestions = self.CS.process("HaLlenBad")
        self.assertListEqual(["Hallenbad"], suggestions)

    def test_arbitrary_chars(self):
        suggestions = self.CS.process("MwDkadfuaSSeeeadfas")
        self.assertIsNone(suggestions)

    # ##########################################################################
    # For the next tests, we change the distance calculator to Levenshtein:

    def test_use_of_levenshtein_corrections(self):
        self.CS.USE_DAMERAU_LEVENSHTEIN = False
        suggestions = self.CS.process("Tset")
        self.assertNotIn("Test", suggestions)
