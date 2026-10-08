import unittest

from parcelq import intake


class ParseParcelTest(unittest.TestCase):
    def test_parses_a_full_row(self):
        row = {"tracking_id": " T9 ", "weight_kg": "2.5", "country": "gb", "recipient": " D. Poet ", "phone": "020 7946 0009", "company": "Poets plc"}
        parcel = intake.parse_parcel(row)
        self.assertEqual((parcel.tracking_id, parcel.weight_kg, parcel.country, parcel.recipient), ("T9", 2.5, "GB", "D. Poet"))
