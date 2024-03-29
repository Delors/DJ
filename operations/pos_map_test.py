import unittest

from common import InitializationFailed
from operations.pos_map import PosMap


class TestPosMap(unittest.TestCase):

    def setUp(self):
        self.posmap = PosMap("ab")

    def test_is_transformer(self):
        self.assertTrue(self.posmap.is_transformer())

    def test__str__(self):
        self.assertEqual(self.posmap.__str__(), 'pos_map "ab"')

    def test_constructor_and_initialization(self):
        posmap = PosMap("")
        self.assertRaises(InitializationFailed,
                          PosMap.init, posmap, None, None)

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
