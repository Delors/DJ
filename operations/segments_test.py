import unittest
import math

from common import InitializationFailed
from operations.segments import Segments


class TestSegments(unittest.TestCase):

    def setUp(self):
        self.S3 = Segments(1, 3)
        self.SInf = Segments(1, math.inf)

    def test_is_extractor(self):
        self.assertTrue(self.S3.is_extractor())

    def test__str__(self):
        self.assertEqual(str(self.S3), "segments 3")
        self.assertEqual(str(self.SInf), "segments inf")

    def test_initr(self):
        s_0_0 = Segments(0, 0)
        s_2_1 = Segments(2, 1)
        self.assertRaises(InitializationFailed, Segments.init,
                          s_0_0, None, None) # segments has no AST dependencies
        self.assertRaises(InitializationFailed, Segments.init,
                          s_2_1, None, None)

    def test_segmentation(self):
        self.assertEqual(self.S3.process("affe"), [
                         "aff", "ffe", "af", "ff", "fe", "a", "f", "f", "e"])
