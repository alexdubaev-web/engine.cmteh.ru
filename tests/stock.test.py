import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from import_stock import match_rows

class StockTests(unittest.TestCase):
 def setUp(self):
  self.products=[{'id':'a','sku':'012345','codes':['012345','ALT-1']},{'id':'b','sku':'RE123','codes':['RE123','ALT-2']}]
 def test_primary_number_keeps_leading_zero_and_parses_count(self):
  result=match_rows([(7,{'C':'012345 ALT-1','D':'12'}),(8,{'C':'RE123','D':'0'})],self.products)
  self.assertEqual(result['a']['quantity'],12);self.assertEqual(result['b']['quantity'],0)
 def test_cross_number_fallback_is_unambiguous(self):
  self.assertEqual(match_rows([(7,{'C':'ALT-1','D':'2'})],self.products)['a']['quantity'],2)
 def test_ambiguity_is_rejected(self):
  with self.assertRaises(ValueError):match_rows([(7,{'C':'012345 RE123','D':'2'})],self.products)
 def test_conflicting_duplicate_is_rejected(self):
  with self.assertRaises(ValueError):match_rows([(7,{'C':'012345','D':'2'}),(8,{'C':'012345','D':'3'})],self.products)
 def test_fractional_or_negative_count_is_rejected(self):
  for qty in ['-1','0.5','NaN']:
   with self.assertRaises(ValueError):match_rows([(7,{'C':'012345','D':qty})],self.products)
 def test_lost_leading_zero_is_not_guessed(self):
  with self.assertRaises(ValueError):match_rows([(7,{'C':'12345','D':'2'})],self.products)

if __name__=='__main__':unittest.main()
