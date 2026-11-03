import unittest

from loyalty import discount_percent, tier


def customer_points(orders):
    """Points earned from a list of order totals in whole currency units: one point per unit."""
    return sum(orders)


class TierTest(unittest.TestCase):
    def test_new_customer_is_basic(self):
        self.assertEqual(tier(customer_points([])), "basic")

    def test_regular_customer_is_silver(self):
        self.assertEqual(tier(customer_points([60, 70])), "silver")


class DiscountTest(unittest.TestCase):
    def test_basic_customers_get_no_discount(self):
        self.assertEqual(discount_percent(customer_points([20])), 0)

    def test_silver_customers_get_five_percent(self):
        self.assertEqual(discount_percent(customer_points([150])), 5)


if __name__ == "__main__":
    unittest.main()
