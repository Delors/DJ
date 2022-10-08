import unittest

import operations.is_keyboard_walk as is_kw

class TestIsKeyboardWalk(unittest.TestCase):

    def setUp(self):
        self.KW = is_kw.IS_KEYBOARD_WALK

    def test_is_filter(self):
        self.assertTrue(self.KW.is_filter())

    def test__str__(self):
        self.assertEqual(self.KW.__str__(),"is_keyboard_walk")

    def test_horizontal_kw(self):        
        self.assertEqual(self.KW.process("asdf"),["asdf"])

    def test_two_horizontal_len4_kw(self):        
        self.assertEqual(self.KW.process("asdfqwert"),["asdfqwert"])

    def test_two_horizontal_len3_kw(self):        
        self.assertEqual(self.KW.process("ioplkj"),["ioplkj"])

    def test_vertical_kw(self):        
        self.assertEqual(self.KW.process("edc"),["edc"])

    def test_no_kw(self):        
        self.assertEqual(self.KW.process("8w1"),[])

    def test_no_kw_due_to_min_length_restriction(self):        
        self.assertEqual(self.KW.process("as"),[])
