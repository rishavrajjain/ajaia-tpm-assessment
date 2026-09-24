# Exception Data Cleaner (Task 2)

## Run it

```bash
python3 normalize_exceptions.py exceptions_raw.csv
python3 test_normalize.py
```

Python 3 standard library only, nothing to install. Output: `exceptions_clean.csv` plus a summary printed to screen.

## Result

```
Exceptions by event type:
  missed_pickup         2   (1 flagged)
  doc_mismatch          2   (1 flagged)
  carrier_substitution  1
  TOTAL                 5   (3 clean, 2 flagged)

Records that could not be confidently cleaned:
  CPX-88215: timestamp is UTC but other records have no timezone - time may be off by several hours, not converted
  CPX-88216: missing carrier code - cannot infer, left blank
```

## Note

The script reads the Terminal 3 export and cleans three fields. It maps `T3` and `Terminal 3` to one terminal name, uppercases carrier codes (`swft`/`Swft` become `SWFT`), and converts all three timestamp formats to `YYYY-MM-DD HH:MM:SS`. Then it counts exceptions by event type. It never drops a record and never guesses. Anything it can't clean with confidence is kept and flagged with a reason. Two records are flagged. CPX-88216 has no carrier code; the other rows suggest SWFT, but guessing a carrier is how a shipment gets routed to the wrong company. CPX-88215 is the only timestamp marked UTC while the rest have no timezone, so converting it could shift it by hours, and that matters for a "late pickup past a threshold" rule. To check that it actually works, not just that it runs, I worked out the expected cleaned value for every record by hand before running it, and the tests compare the output to those exact values. They also check that no rows are dropped, that the counts are right, and that exactly those two records are flagged. A second set of deliberately bad rows (unknown terminal `T9`, ambiguous date `03/04/2026`, a garbage timestamp, a blank or unknown event type, a duplicate ID) must all come back flagged, not silently "cleaned." Finally, I broke the cleaner on purpose (made it guess the blank carrier and stop flagging UTC) and confirmed the tests failed, so they catch real mistakes. The two flags are also the open questions for Corrigan Peak's IT contact on DET-121: does Terminal 3 send local time or UTC, and why is the carrier code sometimes blank?
