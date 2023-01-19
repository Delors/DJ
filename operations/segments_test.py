import unittest
import math

from common import InitializationFailed
from operations.segments import Segments

class TestSegments(unittest.TestCase):

    def setUp(self):
        self.S3 = Segments(3)
        self.SInf = Segments(math.inf)

    def test_is_extractor(self):
        self.assertTrue(self.S3.is_extractor())

    def test__str__(self):
        self.assertEqual(str(self.S3),"segments 3")
        self.assertEqual(str(self.SInf),"segments inf")

    def test_constructor(self):       
        self.assertRaises(InitializationFailed,Segments,0)

    def test_segmentation(self):       
        self.assertEqual(self.S3.process("affe"),["aff","ffe","af","ff","fe","a","f","f","e"])
         
  
  