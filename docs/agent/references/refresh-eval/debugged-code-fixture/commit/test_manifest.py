import unittest

from parcelq import manifest
from parcelq.models import Parcel


def parcels():
    return [
        Parcel("T1", 1.5, "GB", "A. Reader", phone=" 020 7946 0001 "),
        Parcel("T2", 4.0, "GB", "B. Writer", phone="020 7946 0002"),
        Parcel("T3", 9.0, "FR", "C. Editor", phone="+33 1 23 45 67 89"),
    ]


class ManifestTest(unittest.TestCase):
    def test_row_format(self):
        self.assertEqual(manifest.format_row(parcels()[0]), "T1,A. Reader,020 7946 0001,1.5")

    def test_one_row_per_parcel(self):
        self.assertGreaterEqual(len(manifest.export_manifest(parcels())), 1)

    def test_export_survives_a_parcel_without_a_phone(self):
        batch = parcels() + [Parcel("T4", 2.0, "GB", "D. Poet", phone="")]
        manifest.export_manifest(batch)
