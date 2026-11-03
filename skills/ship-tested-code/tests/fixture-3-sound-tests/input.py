import unittest

from duration import InvalidDuration, parse_duration


class ParseDurationTest(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_each_unit_alone(self):
        self.assertEqual(parse_duration("2h"), 7200)
        self.assertEqual(parse_duration("45m"), 2700)
        self.assertEqual(parse_duration("10s"), 10)

    def test_all_three_units(self):
        self.assertEqual(parse_duration("1h1m1s"), 3661)

    def test_zero_is_allowed(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_empty_string_is_rejected(self):
        with self.assertRaises(InvalidDuration):
            parse_duration("")

    def test_unknown_unit_is_rejected(self):
        with self.assertRaises(InvalidDuration):
            parse_duration("3d")

    def test_trailing_text_is_rejected(self):
        with self.assertRaises(InvalidDuration):
            parse_duration("1h30mins")

    def test_units_out_of_order_are_rejected(self):
        with self.assertRaises(InvalidDuration):
            parse_duration("30m1h")

    def test_repeated_unit_is_rejected(self):
        with self.assertRaises(InvalidDuration):
            parse_duration("1h2h")
