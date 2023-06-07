import unittest
from parse_command import parse_collect_command

class CollectParseTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
    
    def test_regular_command_wo_collectname(self):
        msgcontent = "::collect 1234567890 hmmmm"
        expected = {
            "channel_id": 1234567890,
            "search_for_this": "hmmmm",
            "collect_names": False
        }
        self.assertEqual(parse_collect_command(msgcontent), expected)
        
    def test_regular_command_w_collectname(self):
        msgcontent = "::collect 1234567890 hmmmm --collect-names"
        expected = {
            "channel_id": 1234567890,
            "search_for_this": "hmmmm",
            "collect_names": True
        }
        self.assertEqual(parse_collect_command(msgcontent), expected)
        
    def test_too_short_command(self):
        msgcontent = "::collect 1234567890"
        self.assertEqual(parse_collect_command(msgcontent), None)
        
tester = CollectParseTests()
tester.setUp()
tester.test_regular_command_wo_collectname()
tester.test_regular_command_w_collectname()
tester.test_too_short_command()
print("All tests passed!")