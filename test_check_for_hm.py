import unittest
from bot import check_for_hmmm

class HmChecks(unittest.TestCase):
    def setUp(self):
        super().setUp()
    
    def check_len_2(self):
        self.assertEqual(check_for_hmmm('hm'), 2)
    
    def check_len_3(self):
        self.assertEqual(check_for_hmmm('hmm'), 3)
        
    def check_long(self):
        self.assertEqual(check_for_hmmm('hhmmmmmmmmmmmmmmmmmmmmmm'), 23)
        
    def check_messy_str(self):
        self.assertEqual(check_for_hmmm('asdfasdf hmmmmdafadfm'), 5)
    
    def check_two_hms(self):
        self.assertEqual(check_for_hmmm('hm g hmmmmmmmmm'), 2)

test = HmChecks()
test.setUp()
test.check_len_2()
test.check_len_3()
test.check_long()
test.check_messy_str()

print("All tests passed!")