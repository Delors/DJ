import unittest

from operations.pos_map import PosMap

class TestPosMap(unittest.TestCase):

    def setUp(self):
        self.posmap = PosMap("ab")

    def test_is_transformer(self):
        self.assertTrue(self.posmap.is_transformer())

    def test__str__(self):
        self.assertEqual(self.posmap.__str__(),"pos_map [ab]")

    def test_constructor(self):       
        self.assertRaises(ValueError, PosMap,"")

    def test_map(self):       
        self.assertEqual(
            self.posmap.process("Test"),
            [
                "best",
                "aest",
                "Tbst",
                "Tast",
                "Tebt",
                "Teat",
                "Tesb",
                "Tesa"
            ]
        )
  