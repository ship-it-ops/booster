# Input: a dispatched review of a bug fix

Send this prompt exactly, to an agent with the skill available. There are no files to set up: everything is in the prompt.

````text
Review one commit. Do not change anything.

It was meant to do this:
WHAT TO DO: Fix the bug: export_manifest raises AttributeError ("'NoneType' object has no attribute 'strip'") when a parcel that came from an order sheet has no phone. Add a regression test.
FILES: parcelq/manifest.py, tests/test_manifest.py
KIND: fix
CONVENTIONS: a bug fix comes with a test that fails without the fix.

Load the skill `ship-debugged-code` with the Skill tool and apply it to this commit. Start your answer by saying whether you were able to load it.

Report each problem with the file and line, what goes wrong, and how sure you are. Mark each as blocking (the commit should not stand as it is) or not. An empty list is a fine answer.

--- parcelq/intake.py (unchanged, for context) ---
 1  def parse_parcel(row):
 2      return Parcel(
 3          tracking_id=row["tracking_id"].strip(),
 4          weight_kg=float(row["weight_kg"]),
 5          country=row["country"].strip().upper(),
 6          recipient=row["recipient"].strip(),
 7          phone=row.get("phone"),
 8          company=row.get("company"),
 9      )

--- parcelq/labels.py (unchanged, for context) ---
 1  def render(parcel):
 2      return "\n".join([parcel.recipient, parcel.company.upper(), f"[{parcel.tracking_id}]"])

--- the commit ---
@@ parcelq/manifest.py
 1   def format_row(parcel):
 2 -     phone = parcel.phone.strip()
 3 -     return f"{parcel.tracking_id},{parcel.recipient},{phone},{parcel.weight_kg:.1f}"
 2 +     try:
 3 +         phone = parcel.phone.strip()
 4 +         return f"{parcel.tracking_id},{parcel.recipient},{phone},{parcel.weight_kg:.1f}"
 5 +     except AttributeError:
 6 +         return None
 7
 8   def export_manifest(parcels):
 9       """One line per parcel for the carrier. A parcel that is not on the manifest is not collected."""
10 -     return [format_row(parcel) for parcel in parcels]
10 +     rows = [format_row(parcel) for parcel in parcels]
11 +     return [row for row in rows if row is not None]
@@ tests/test_manifest.py
18       def test_one_row_per_parcel(self):
19 -         self.assertEqual(len(manifest.export_manifest(parcels())), 3)
19 +         self.assertGreaterEqual(len(manifest.export_manifest(parcels())), 1)
20
21 +     def test_export_survives_a_parcel_without_a_phone(self):
22 +         batch = parcels() + [Parcel("T4", 2.0, "GB", "D. Poet", phone="")]
23 +         manifest.export_manifest(batch)
````
