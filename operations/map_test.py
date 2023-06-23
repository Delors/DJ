import unittest

from common import InitializationFailed
from operations.map import Map


class TestMap(unittest.TestCase):

    def setUp(self):
        self.map_a_to_1 = Map(False, "a", "1")
        self.map_a_to_1.init(None, None)  # map has no AST dependencies
        self.map_b_to_1_and_2 = Map(False, "b", "12")
        self.map_b_to_1_and_2.init(None, None)

    def test_is_transformer(self):
        self.assertTrue(self.map_a_to_1.is_transformer())

    def test__str__(self):
        self.assertEqual(self.map_b_to_1_and_2.__str__(), 'map "b" "12"')
        self.assertEqual(self.map_a_to_1.__str__(), 'map "a" "1"')

    def test_init(self):
        map = Map(False, "a", "a")
        self.assertRaises(InitializationFailed, Map.init,
                          map, None, None)  # map has no AST dependencies

    def test_single_map(self):
        self.assertEqual(self.map_a_to_1.process("affe"), ["1ffe"])

    def test_multi_map(self):
        self.assertFalse(
            set(self.map_b_to_1_and_2.process("baby")).
            isdisjoint(
                set(["1a1y", "2a2y"]))
        )
