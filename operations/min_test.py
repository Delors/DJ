import unittest

from operations.min import Min


class TestMin(unittest.TestCase):

    def setUp(self):
        self.mln_2 = Min("length", 2)
        self.mlo_2 = Min("lower", 2)
        self.mup_2 = Min("upper", 2)
        self.mnu_2 = Min("numeric", 2)
        self.mle_2 = Min("letter", 2)
        self.msy_2 = Min("symbol", 2)
        self.mnl_2 = Min("non_letter", 2)

    def test_is_filter(self):
        self.assertTrue(self.mln_2.is_filter())
        self.assertTrue(self.mlo_2.is_filter())
        self.assertTrue(self.mup_2.is_filter())
        self.assertTrue(self.mnu_2.is_filter())
        self.assertTrue(self.mle_2.is_filter())
        self.assertTrue(self.msy_2.is_filter())
        self.assertTrue(self.mnl_2.is_filter())

    def test__str__(self):
        self.assertEqual(self.mln_2.__str__(), "min length 2")
        self.assertEqual(self.mlo_2.__str__(), "min lower 2")
        self.assertEqual(self.mup_2.__str__(), "min upper 2")
        self.assertEqual(self.mnu_2.__str__(), "min numeric 2")
        self.assertEqual(self.mle_2.__str__(), "min letter 2")
        self.assertEqual(self.msy_2.__str__(), "min symbol 2")
        self.assertEqual(self.mnl_2.__str__(), "min non_letter 2")

    def test_no_respective_chars(self):
        self.assertListEqual(self.mlo_2.process("ABC"), [])
        self.assertListEqual(self.mup_2.process("abc"), [])
        self.assertListEqual(self.mnu_2.process("ABC"), [])
        self.assertListEqual(self.mle_2.process("111"), [])
        self.assertListEqual(self.msy_2.process("ABC"), [])
        self.assertListEqual(self.mnl_2.process("ABC"), [])

    def test_to_few_respective_chars(self):
        self.assertListEqual(self.mlo_2.process("aBC"), [])
        self.assertListEqual(self.mup_2.process("Abc"), [])
        self.assertListEqual(self.mnu_2.process("1BC"), [])
        self.assertListEqual(self.mle_2.process("1a1"), [])
        self.assertListEqual(self.msy_2.process("$BC"), [])
        self.assertListEqual(self.mnl_2.process("2BC"), [])
        self.assertListEqual(self.mnl_2.process("$BC"), [])

    def test_enough_respective_chars(self):
        self.assertListEqual(self.mlo_2.process("abC"), ["abC"])
        self.assertListEqual(self.mup_2.process("ABc"), ["ABc"])
        self.assertListEqual(self.mnu_2.process("1a2"), ["1a2"])
        self.assertListEqual(self.mle_2.process("a2_B"), ["a2_B"])
        self.assertListEqual(self.msy_2.process("$_BC"), ["$_BC"])
        self.assertListEqual(self.mnl_2.process("BC22"), ["BC22"])
        self.assertListEqual(self.mnl_2.process("BC#'"), ["BC#'"])
        self.assertListEqual(self.mnl_2.process("BC#2"), ["BC#2"])
