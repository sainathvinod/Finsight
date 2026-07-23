# Verifies: NFR-059, FR-014
import unittest
from decimal import Decimal
from finsight.domain.money import to_decimal, pct, money_str

class TestMoney(unittest.TestCase):
    def test_parse_and_placeholder(self):
        self.assertEqual(to_decimal("1,234.56"), Decimal("1234.56"))
        self.assertIsNone(to_decimal("."))
        self.assertIsNone(to_decimal(""))
    def test_pct_exact(self):
        self.assertEqual(pct(Decimal("3000"), Decimal("10000")), Decimal("30.00"))
        self.assertIsNone(pct(Decimal("1"), Decimal("0")))
    def test_no_float(self):
        self.assertIsInstance(to_decimal("0.1"), Decimal)
        self.assertEqual(money_str(Decimal("13000")), "13000.00")

if __name__ == "__main__":
    unittest.main()
