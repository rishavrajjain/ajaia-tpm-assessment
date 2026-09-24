# Ajaia Technical Project Manager Assessment

**Video:** [VIDEO LINK — paste here]

**Candidate:** [Your name]
**Build files:** [link to repo/folder with `normalize_exceptions.py`, `test_normalize.py`, `exceptions_raw.csv`]
**Other work (optional):** [GitHub / past builds, or delete this line]

Prepared for [Ajaia](https://ajaia.ai): Corrigan Peak Logistics, Dispatch Exception Triage engagement.

---

## Task 1. Triage

| Rank | Item | This week | Why |
|---|---|---|---|
| **1** | **C. Terminal 3 scores are empty (DET-121)** | **Worked today.** I ask Corrigan Peak's IT contact exactly which fields Terminal 3 sends and ask for an answer within 2 days. Until it's fixed: if an exception has no score, don't guess. Send it to a "Needs manual review" queue that a named dispatcher checks. | One of three terminals is partly invisible to the tool. We can't fix it until the client answers, so every day we wait is lost. It was flagged on Aug 6 and nobody followed up, so I'm taking it on. |
| **2** | **B. Priya's bug: the same exception can be sent twice** | **Worked today.** The code doesn't go live until it's fixed. Priya fixes it, and I make sure it's tested for both cases she named (the database update failing after a push, and two poll cycles overlapping). | Cheap to fix now, costly after launch. If dispatchers get duplicate alerts, they stop trusting the tool, which is the problem we're here to solve. |
| **3** | **D. Nobody has contacted the terminal leads (DET-118)** | **Worked today.** I contact the three terminal leads and book the routing-rules review. | If the routing rules are wrong, exceptions go to the wrong dispatcher on day one. It takes 15 minutes, and it was stuck only because nobody owned it. |
| **4** | **A. Dana: auto-reassign missed pickups to a backup carrier** | **Declined for Sept 8.** Offered as Phase 2, with a clear reason Dana can pass to her COO. | Today the tool flags problems for a human to decide. This would have it move real shipments to another carrier on its own, which is hard to undo. With bug B, it could even reassign the same shipment twice. |
| **5** | **E. Marcus: change the shade of blue** | **Clarify, then decide.** Marcus asks ops which exact colour and whether they need it for launch. If it's specific and tiny, it goes on the final UI polish list after the work above. Otherwise it waits until after launch. | **This is the noise.** It came up in passing, it doesn't change whether the tool works, and it shouldn't take Priya's time from items that could break the launch. |

**How I ranked them:** what could break the launch, and whether we control the timeline. C is first because we're waiting on the client. B is fully in our hands. D is small but important. A and E can wait until after go-live.

**How the date is protected (what's cut and what moves):**
- **Cut from Sept 8:** auto-reassign (A). Offered as Phase 2.
- **Moved to post-launch unless confirmed tiny:** the colour change (E).
- **Fallback if Terminal 3 answers come late:** launch on Sept 8 with Terminal 3 exceptions going to the manual-review queue until the fix lands. Every exception still reaches a person; some just aren't scored automatically yet.
- **Not assumed:** that the team will "just work faster."

---

## Task 2. Build

**Files:** `normalize_exceptions.py` (script), `test_normalize.py` (tests), `exceptions_raw.csv` (Material 3 as given). Python 3 standard library only, nothing to install.

```bash
python3 normalize_exceptions.py exceptions_raw.csv
python3 test_normalize.py
```

**Output:**

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

**Note:** The script reads the Terminal 3 export and cleans three fields. It maps `T3` and `Terminal 3` to one terminal name, uppercases carrier codes (`swft`/`Swft` become `SWFT`), and converts all three timestamp formats to `YYYY-MM-DD HH:MM:SS`. Then it counts exceptions by event type. It never drops a record and never guesses. Anything it can't clean with confidence is kept and flagged with a reason. Two records are flagged. CPX-88216 has no carrier code; the other rows suggest SWFT, but guessing a carrier is how a shipment gets routed to the wrong company. CPX-88215 is the only timestamp marked UTC while the rest have no timezone, so converting it could shift it by hours, and that matters for a "late pickup past a threshold" rule. To check that it actually works, not just that it runs, I worked out the expected cleaned value for every record by hand before running it, and the tests compare the output to those exact values. They also check that no rows are dropped, that the counts are right, and that exactly those two records are flagged. A second set of deliberately bad rows (unknown terminal `T9`, ambiguous date `03/04/2026`, a garbage timestamp, a blank or unknown event type, a duplicate ID) must all come back flagged, not silently "cleaned." Finally, I broke the cleaner on purpose (made it guess the blank carrier and stop flagging UTC) and confirmed 6 tests failed, so the tests catch real mistakes. The two flags are also the open questions for Corrigan Peak's IT contact on DET-121: does Terminal 3 send local time or UTC, and why is the carrier code sometimes blank?

---

## Task 3. Client status update

**To:** Dana Okafor, VP Operations, Corrigan Peak Logistics
**Subject:** Dispatch Exception Triage: Weekly Status, Amber (a correction and two asks)

Hi Dana,

**Status: Amber.** September 8 is still achievable, but it now depends on two things from your team this week. I also need to correct last Friday's update.

**Correction to last week.** We reported Green with no blockers and called Terminal 3 a minor data validation task. That understated it. Right now, a share of Terminal 3 exceptions get no urgency score, which means the tool can't route them to a dispatcher. We should have flagged this more clearly. I now own it directly.

**What's on track.** Ingestion, scoring and routing are working, and the dispatcher queue UI is on track for your team's review next week.

**What we need from you**

1. **Terminal 3 data: answers from your IT contact by Wednesday.** We need three things confirmed:
   - Which fields Terminal 3 sends from FreightWorks.
   - Whether Terminal 3 timestamps are local time or UTC, and which timezone Terminal 3 is in. We're seeing both in the same export.
   - Whether the carrier code can be blank, and why.

   Once we have the answers, the fix is about 2 days plus testing. **If we don't have answers by Friday,** we recommend going live on September 8 with Terminal 3 exceptions sent to a manual-review queue checked by a named dispatcher until the fix lands. Every exception would still reach a person; some just wouldn't be scored automatically at first. I'd rather agree that fallback with you now than decide it in launch week.

2. **Routing-rules review with your three terminal leads.** We're reaching out to them today to book a one-hour session. It needs to happen by next Wednesday so any rule changes go in before launch. A nudge from you would help get it onto their calendars.

**Also this week**
- **Reliability fix.** Our internal code review found a case where the same exception could be sent to a dispatcher twice. It's being fixed and tested before it ships. No impact on the date.
- **Safety net.** Until Terminal 3 is fixed, anything the tool can't score goes to manual review, so nothing is silently dropped.

**Your COO's request for auto-reassign.** We recommend not adding it for September 8. It would change the tool from flagging a missed pickup for a dispatcher to moving the shipment to another carrier on its own. That touches carrier agreements, and it's hard to undo if it gets one wrong. Doing it safely needs backup-carrier rules, proper testing and an undo path, and we can't responsibly build those in three weeks. What you can tell him: on September 8, missed pickups go straight to the right dispatcher instead of a shared inbox. The first weeks of live data will show how often missed pickups happen and how dispatchers resolve them, which is exactly what we need to design auto-reassign well. We'll send you a Phase 2 outline by the end of next week, and I'm happy to join that conversation with him if it helps.

Next update Friday, or sooner if the Terminal 3 answers change the picture.

Best,
[Your name]
Technical Project Manager, Ajaia ([ajaia.ai](https://ajaia.ai))

---

## Task 4. AI workflow note

I used Claude on every task. I used it to break down the assignment, pressure-test my triage ranking, draft the status update, and write the cleaning script and its tests. I kept the calls human: the ranking, declining auto-reassign, moving the status to Amber, and the rule that the script must never guess a carrier or silently convert a timezone. I also changed some of the AI's output. It first said to simply defer the colour request. I changed that to "clarify which colour first," because a two-minute question beats guessing and redoing work. It also added a launch-calendar point that I cut, because it didn't change any decision. And it wrote some steps in jargon, such as "route null-score exceptions to a manual-review queue," which I rewrote in plain language before it went near the client. For the build, I didn't trust "it ran." I checked the output against hand-worked values, and I had the script broken on purpose to confirm the tests actually fail when it guesses the carrier or stops flagging UTC.
