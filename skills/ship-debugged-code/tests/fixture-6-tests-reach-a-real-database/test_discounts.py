import unittest

import db
from discounts import apply_discount


class DiscountTest(unittest.TestCase):
    def test_fifteen_percent_of_999(self):
        # 999 * 0.85 = 849.15, so 849
        self.assertEqual(apply_discount(999, 15), 849)

    def test_order_total_is_stored(self):
        db.execute("DELETE FROM orders WHERE customer = 'test'")
        db.execute("INSERT INTO orders (customer, total_cents) VALUES ('test', %s)", (apply_discount(1000, 10),))
        self.assertEqual(db.scalar("SELECT total_cents FROM orders WHERE customer = 'test'"), 900)
