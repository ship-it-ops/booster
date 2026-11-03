import unittest

from totals import order_total


class OrderTotalTest(unittest.TestCase):
    def test_two_lines(self):
        lines = [{"quantity": 2, "unit_price_cents": 150}, {"quantity": 1, "unit_price_cents": 990}]
        self.assertEqual(order_total(lines), 1290)
