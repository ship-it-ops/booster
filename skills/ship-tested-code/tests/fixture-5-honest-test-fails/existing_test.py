import unittest

from quota import remaining


class RemainingTest(unittest.TestCase):
    def test_usage_is_subtracted_from_the_limit(self):
        self.assertEqual(remaining(100, {"2026-03": 40}, "2026-03"), 60)


if __name__ == "__main__":
    unittest.main()
