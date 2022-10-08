import unittest

from operations.map import Map

class TestMap(unittest.TestCase):

    def setUp(self):
        self.map_a_to_1 = Map("a","1")
        self.map_b_to_1_and_2 = Map("b","12")

    def test_is_transformer(self):
        self.assertTrue(self.map_a_to_1.is_transformer())

    def test__str__(self):
        self.assertEqual(self.map_b_to_1_and_2.__str__(),"map b [12]")
        self.assertEqual(self.map_a_to_1.__str__(),"map a [1]")

    def test_constructor(self):       
        self.assertRaises(ValueError, Map,"a","a")

    def test_single_map(self):       
        self.assertEqual(self.map_a_to_1.process("affe"),["1ffe"])
         
    def test_multi_map(self):       
        self.assertFalse(
            set(self.map_b_to_1_and_2.process("baby")).\
                isdisjoint(
                    set(["1a1y","2a2y"]))
        )
  