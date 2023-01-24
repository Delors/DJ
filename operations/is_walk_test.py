import unittest

import operations.is_walk as is_kw


class TestIsWalk(unittest.TestCase):

    def setUp(self):
        is_kw.IsWalk.LAYOUT = "KEYBOARD_DE"
        is_kw.IsWalk.MIN_SUB_WALK_LENGTH = 3
        is_kw.IsWalk.MIN_WALK_LENGTH = 3
        self.KW = is_kw.IsWalk()

        is_kw.IsWalk.LAYOUT = "PIN_PAD"
        is_kw.IsWalk.MIN_SUB_WALK_LENGTH = float('inf')
        is_kw.IsWalk.MIN_WALK_LENGTH = 3
        self.PW = is_kw.IsWalk()

    def test_is_filter(self):
        self.assertTrue(self.KW.is_filter())

    def test__str__(self):
        self.assertEqual(self.KW.__str__(), "is_walk")

    def test_horizontal_kw(self):
        self.assertEqual(self.KW.process("asdf"), ["asdf"])

    def test_two_horizontal_len4_kw(self):
        self.assertEqual(self.KW.process("asdfqwert"), ["asdfqwert"])

    def test_two_horizontal_len3_kw(self):
        self.assertEqual(self.KW.process("ioplkj"), ["ioplkj"])

    def test_vertical_kw(self):
        self.assertEqual(self.KW.process("edc"), ["edc"])

    def test_no_kw(self):
        self.assertEqual(self.KW.process("8w1"), [])

    def test_no_kw_due_to_min_length_restriction(self):
        self.assertEqual(self.KW.process("as"), [])

    def test_pw_selection(self):
        # The following is "only" a walk on a pin pad!
        self.assertEqual(self.KW.process("1236"), ["1236"])

    def test_pw_inf_sub_walk_length(self):
        # The following is "only" a walk on a pin pad!
        self.assertEqual(self.PW.process("123654123654123654123654123654"), [
                         "123654123654123654123654123654"])
        # The following are "two" disconnected walks on a pin pad!
        self.assertEqual(self.PW.process(
            "123654123654123654123654123654987"), [])
