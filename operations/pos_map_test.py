import unittest

from common import InitializationFailed
from operations.pos_map import PosMap

class TestPosMap(unittest.TestCase):

    def setUp(self):
        self.posmap = PosMap("ab")

    def test_is_transformer(self):
        self.assertTrue(self.posmap.is_transformer())

    def test__str__(self):
        self.assertEqual(self.posmap.__str__(),'pos_map "ab"')

    def test_constructor(self):       
        self.assertRaises(InitializationFailed, PosMap,"")

    def test_map(self):       
        self.assertEqual(
            set(self.posmap.process("Test")),
            set([
                "aest",
                "best",                
                "Tast",
                "Tbst",
                "Teat",
                "Tebt",
                "Tesa",
                "Tesb"                
            ])
        )
  