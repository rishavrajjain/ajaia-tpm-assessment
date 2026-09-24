"""
Checks that the cleaner produces the RIGHT answer, not just that it runs.

Run:  python3 test_normalize.py
"""
import csv
import re
import unittest
from collections import Counter

from normalize_exceptions import clean_rows

TS_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def load_raw():
    with open("exceptions_raw.csv", newline="") as f:
        return list(csv.DictReader(f))


class TestRealExport(unittest.TestCase):
    """The 5 records Corrigan Peak sent, checked against hand-worked answers."""

    def setUp(self):
        self.raw = load_raw()
        self.cleaned = clean_rows(self.raw)
        self.by_id = {r["exception_id"]: r for r in self.cleaned}

    def test_no_records_dropped(self):
        self.assertEqual(len(self.raw), 5)
        self.assertEqual(len(self.cleaned), 5)

    def test_counts_by_event_type(self):
        counts = Counter(r["event_type"] for r in self.cleaned)
        self.assertEqual(counts, {"missed_pickup": 2, "doc_mismatch": 2,
                                  "carrier_substitution": 1})

    def test_exactly_the_two_expected_records_are_flagged(self):
        flagged = {r["exception_id"] for r in self.cleaned if r["status"] == "flagged"}
        self.assertEqual(flagged, {"CPX-88215", "CPX-88216"})

    def test_terminals_all_normalized(self):
        self.assertTrue(all(r["terminal"] == "Terminal 3" for r in self.cleaned))

    def test_carrier_codes_uppercase_or_flagged(self):
        for r in self.cleaned:
            if r["carrier_code"]:
                self.assertTrue(r["carrier_code"].isupper())
            else:
                self.assertEqual(r["status"], "flagged")

    def test_blank_carrier_is_not_guessed(self):
        self.assertEqual(self.by_id["CPX-88216"]["carrier_code"], "")
        self.assertIn("missing carrier", self.by_id["CPX-88216"]["flag_reason"])

    def test_timestamps_one_format(self):
        for r in self.cleaned:
            self.assertRegex(r["event_ts"], TS_PATTERN)

    def test_exact_cleaned_values(self):
        # Worked out by hand before running the script.
        expected = {
            "CPX-88213": ("SWFT", "2026-08-14 09:12:00"),
            "CPX-88214": ("SWFT", "2026-08-14 09:45:00"),
            "CPX-88215": ("SWFT", "2026-08-14 10:03:00"),
            "CPX-88216": ("",     "2026-08-14 11:47:00"),
            "CPX-88217": ("RLCX", "2026-08-15 08:02:00"),
        }
        for eid, (carrier, ts) in expected.items():
            self.assertEqual(self.by_id[eid]["carrier_code"], carrier, eid)
            self.assertEqual(self.by_id[eid]["event_ts"], ts, eid)

    def test_utc_record_flagged_not_converted(self):
        r = self.by_id["CPX-88215"]
        self.assertEqual(r["event_ts"], "2026-08-14 10:03:00")  # clock time kept
        self.assertIn("UTC", r["flag_reason"])


class TestDirtyData(unittest.TestCase):
    """Deliberately bad rows: every one must be FLAGGED, never silently 'cleaned'."""

    def clean_one(self, **overrides):
        row = {"exception_id": "X-1", "terminal": "Terminal 3",
               "event_type": "missed_pickup", "carrier_code": "SWFT",
               "event_ts": "2026-08-14 09:12:00"}
        row.update(overrides)
        return clean_rows([row])[0]

    def test_good_row_is_clean(self):
        self.assertEqual(self.clean_one()["status"], "clean")

    def test_unknown_terminal(self):
        r = self.clean_one(terminal="T9")
        self.assertEqual(r["status"], "flagged")
        self.assertEqual(r["terminal"], "T9")

    def test_ambiguous_date(self):
        self.assertEqual(self.clean_one(event_ts="03/04/2026 10:00")["status"], "flagged")

    def test_garbage_timestamp(self):
        self.assertEqual(self.clean_one(event_ts="garbage")["status"], "flagged")

    def test_blank_event_type(self):
        self.assertEqual(self.clean_one(event_type="")["status"], "flagged")

    def test_unknown_event_type(self):
        self.assertEqual(self.clean_one(event_type="flat_tire")["status"], "flagged")

    def test_duplicate_exception_id(self):
        row = {"exception_id": "X-1", "terminal": "T3", "event_type": "doc_mismatch",
               "carrier_code": "RLCX", "event_ts": "2026-08-14 09:12:00"}
        results = clean_rows([row, dict(row)])
        self.assertEqual(results[0]["status"], "clean")
        self.assertEqual(results[1]["status"], "flagged")


if __name__ == "__main__":
    unittest.main(verbosity=2)
