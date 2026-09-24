"""
Clean Corrigan Peak exception records and summarize them by event type.

Usage:
    python3 normalize_exceptions.py exceptions_raw.csv [exceptions_clean.csv]

Rules:
  - Never drop a record. If something can't be cleaned confidently, keep the
    row, mark it "flagged", and say why.
  - Never guess. A blank carrier stays blank; an unknown terminal stays as-is.
"""
import csv
import re
import sys
from collections import Counter
from datetime import datetime

# Every spelling we have seen (or expect) for each terminal.
TERMINAL_ALIASES = {
    "terminal 1": "Terminal 1", "terminal1": "Terminal 1", "t1": "Terminal 1",
    "terminal 2": "Terminal 2", "terminal2": "Terminal 2", "t2": "Terminal 2",
    "terminal 3": "Terminal 3", "terminal3": "Terminal 3", "t3": "Terminal 3",
}

KNOWN_EVENT_TYPES = {"missed_pickup", "doc_mismatch", "carrier_substitution"}

OUTPUT_TS_FORMAT = "%Y-%m-%d %H:%M:%S"

OUTPUT_COLUMNS = ["exception_id", "terminal", "event_type", "carrier_code",
                  "event_ts", "status", "flag_reason"]


def clean_terminal(value):
    key = " ".join(value.strip().lower().split())
    if key in TERMINAL_ALIASES:
        return TERMINAL_ALIASES[key], None
    return value.strip(), f"unknown terminal '{value.strip()}' - not guessed"


def clean_carrier(value):
    code = value.strip().upper()
    if not code:
        return "", "missing carrier code - cannot infer, left blank"
    if not re.fullmatch(r"[A-Z]{2,4}", code):
        return code, f"carrier code '{code}' is not 2-4 letters"
    return code, None


def clean_timestamp(value):
    """Return (standard timestamp, reason-or-None).

    Only the formats actually seen in the export are accepted. Anything else
    is flagged instead of guessed.
    """
    raw = value.strip()
    if not raw:
        return "", "missing timestamp"

    # 1. 2026-08-14 09:12:00  (no timezone)
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").strftime(OUTPUT_TS_FORMAT), None
    except ValueError:
        pass

    # 2. 08/14/2026 09:45  (month/day/year, no seconds, no timezone)
    try:
        ts = datetime.strptime(raw, "%m/%d/%Y %H:%M")
        if ts.month <= 12 and ts.day <= 12 and ts.month != ts.day:
            return ts.strftime(OUTPUT_TS_FORMAT), (
                f"ambiguous date '{raw}' - could be month/day or day/month")
        return ts.strftime(OUTPUT_TS_FORMAT), None
    except ValueError:
        pass

    # 3. 2026-08-14T10:03:00Z  (UTC). The other formats carry no timezone,
    #    so converting would be a guess. Standardize the format, keep the
    #    clock time, and flag it.
    try:
        ts = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
        return ts.strftime(OUTPUT_TS_FORMAT), (
            "timestamp is UTC but other records have no timezone - "
            "time may be off by several hours, not converted")
    except ValueError:
        pass

    return raw, f"unrecognized timestamp format '{raw}'"


def clean_event_type(value):
    event = value.strip().lower()
    if not event:
        return "", "missing event type"
    if event not in KNOWN_EVENT_TYPES:
        return event, f"unknown event type '{event}'"
    return event, None


def clean_rows(rows):
    cleaned = []
    seen_ids = set()
    for row in rows:
        reasons = []
        exception_id = (row.get("exception_id") or "").strip()
        if exception_id in seen_ids:
            reasons.append("duplicate exception_id")
        seen_ids.add(exception_id)

        terminal, r1 = clean_terminal(row.get("terminal") or "")
        event_type, r2 = clean_event_type(row.get("event_type") or "")
        carrier, r3 = clean_carrier(row.get("carrier_code") or "")
        event_ts, r4 = clean_timestamp(row.get("event_ts") or "")
        reasons += [r for r in (r1, r2, r3, r4) if r]

        cleaned.append({
            "exception_id": exception_id,
            "terminal": terminal,
            "event_type": event_type,
            "carrier_code": carrier,
            "event_ts": event_ts,
            "status": "flagged" if reasons else "clean",
            "flag_reason": "; ".join(reasons),
        })
    return cleaned


def summarize(cleaned):
    totals = Counter(r["event_type"] or "(missing)" for r in cleaned)
    flagged = Counter(r["event_type"] or "(missing)" for r in cleaned
                      if r["status"] == "flagged")
    n_flagged = sum(flagged.values())

    lines = ["Exceptions by event type:"]
    for event, count in totals.most_common():
        note = f"   ({flagged[event]} flagged)" if flagged[event] else ""
        lines.append(f"  {event:<22}{count}{note}")
    lines.append(f"  {'TOTAL':<22}{len(cleaned)}   "
                 f"({len(cleaned) - n_flagged} clean, {n_flagged} flagged)")

    lines.append("")
    lines.append("Records that could not be confidently cleaned:")
    problems = [r for r in cleaned if r["status"] == "flagged"]
    if not problems:
        lines.append("  none")
    for r in problems:
        lines.append(f"  {r['exception_id']}: {r['flag_reason']}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "exceptions_clean.csv"

    with open(in_path, newline="") as f:
        rows = list(csv.DictReader(f))

    cleaned = clean_rows(rows)

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"Read {len(rows)} records from {in_path}, wrote {len(cleaned)} to {out_path}\n")
    print(summarize(cleaned))


if __name__ == "__main__":
    main()
