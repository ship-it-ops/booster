import unittest

from parcelq import labels
from parcelq.models import Parcel


class LabelTest(unittest.TestCase):
    def test_label_lines(self):
        parcel = Parcel("T1", 1.5, "GB", "A. Reader", company="Readers Ltd")
        self.assertEqual(labels.render(parcel), "A. Reader\nREADERS LTD\nGB\n[T1]")
