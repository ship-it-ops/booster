import unittest

from inventory.legacy import load_legacy


class LegacyTests(unittest.TestCase):
    def test_loads_three_rows(self):
        self.assertEqual(len(load_legacy()), 3)


if __name__ == "__main__":
    unittest.main()
