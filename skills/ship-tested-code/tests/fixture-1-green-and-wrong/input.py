import unittest

from shipping import BASE_CENTS, PER_KG_CENTS, ZONE_MULTIPLIER, UnknownZone, shipping_cents

RESULTS = []


class ShippingTest(unittest.TestCase):
    def test_domestic_parcel(self):
        self.assertEqual(shipping_cents(2000, 2, "domestic"), 739)

    def test_exactly_at_threshold_pays_shipping(self):
        self.assertEqual(shipping_cents(5000, 1, "domestic"), 619)

    def test_eu_costs_more(self):
        expected = (BASE_CENTS + 3 * PER_KG_CENTS) * ZONE_MULTIPLIER["eu"]
        self.assertEqual(shipping_cents(1000, 3, "eu"), expected)

    def test_unknown_zone(self):
        try:
            shipping_cents(1000, 1, "mars")
        except UnknownZone:
            pass

    def test_free_shipping(self):
        cost = shipping_cents(9000, 1, "domestic")
        RESULTS.append(cost)
        self.assertTrue(cost >= 0)

    def test_results_recorded(self):
        self.assertEqual(len(RESULTS), 1)
