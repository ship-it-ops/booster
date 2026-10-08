import unittest
from datetime import date, datetime, timezone
from unittest import mock

from parcelq import pickup


class PickupDateTest(unittest.TestCase):
    def test_same_day_before_cutoff(self):
        morning = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
        with mock.patch("parcelq.clock.now", return_value=morning):
            self.assertEqual(pickup.pickup_date(), date(2026, 3, 10))
