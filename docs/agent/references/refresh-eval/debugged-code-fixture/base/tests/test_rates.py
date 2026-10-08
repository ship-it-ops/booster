import unittest

from parcelq import rates


class LoadTableTest(unittest.TestCase):
    def setUp(self):
        rates.clear_cache()

    def test_domestic_bands_are_cheapest_first(self):
        prices = [band["price_cents"] for band in rates.load_table("domestic")]
        self.assertEqual(prices, [450, 890, 1990])

    def test_second_load_returns_the_cached_object(self):
        self.assertIs(rates.load_table("domestic"), rates.load_table("domestic"))

    def test_round_half_up(self):
        self.assertEqual(rates.round_half_up_cents(10.5), 11)
        self.assertEqual(rates.round_half_up_cents(10.4), 10)
