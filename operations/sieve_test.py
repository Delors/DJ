import unittest

from operations.sieve import Sieve

class TestMin(unittest.TestCase):

    def setUp(self):
        self.s = Sieve("sieve/graphene_os_12_password_chars.txt")

    def test_is_filter(self):
        self.assertTrue(self.s.is_filter())

    def test__str__(self):
        self.assertEqual(self.s.__str__(),"sieve \"sieve/graphene_os_12_password_chars.txt\"")

    def test_process_filter(self):
        self.assertListEqual(self.s.process("§bgb"),[])
        self.assertListEqual(self.s.process("üöä"),[])        

    def test_process_pass(self):
        self.assertListEqual(self.s.process(" "),[" "])
        self.assertListEqual(self.s.process("!?Yes1234"),["!?Yes1234"])
        all_valid = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890@#$%&-+()*\"':;!?,_ /.~`|·✓π÷×¶△£¢€¥^°={}\©®™℅[],< >."
        self.assertListEqual(self.s.process(all_valid),[all_valid])
