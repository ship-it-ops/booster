import unittest

from parcelq import quotes, rates
from parcelq.models import Parcel


def parcel(weight_kg, country="GB"):
    return Parcel(tracking_id="T1", weight_kg=weight_kg, country=country, recipient="A. Reader")


class QuoteTest(unittest.TestCase):
    def setUp(self):
        rates.clear_cache()

    def test_light_domestic_parcel(self):
        self.assertEqual(quotes.quote(parcel(1.5)), 450)

    def test_international_parcel(self):
        self.assertEqual(quotes.quote(parcel(5, country="FR")), 3200)

    def test_too_heavy(self):
        with self.assertRaises(ValueError):
            quotes.quote(parcel(31))

    def test_promotion_applies_to_the_customer_who_has_it(self):
        promotion = {"max_kg": 5, "price_cents": 300}
        self.assertEqual(quotes.quote(parcel(1.5), promotion=promotion), 300)

    def test_fuel_surcharge(self):
        self.assertEqual(quotes.quote_with_fuel_surcharge(parcel(1.5), 10), 495)
