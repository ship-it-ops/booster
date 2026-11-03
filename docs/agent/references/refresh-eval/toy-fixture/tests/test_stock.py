import unittest

from inventory.stock import total


class TotalTests(unittest.TestCase):
    def test_total_sums_quantities(self):
        self.assertEqual(total([{"sku": "A", "qty": 2}, {"sku": "B", "qty": 3}]), 5)

    def test_total_empty_is_zero(self):
        self.assertEqual(total([]), 0)


if __name__ == "__main__":
    unittest.main()
