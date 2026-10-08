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
