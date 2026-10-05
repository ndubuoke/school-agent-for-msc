---
name: find-schools
description: Research master's programs (Information Systems, IT Management, Cloud/DevOps, Systems, Technology Management) in a country, province/state, or region, verify facts from official university sources, check eligibility against profile.md, score against criteria.md, and update the tracker, reports and a ranked Top 10. Use when the user runs /find-schools or asks to find, research, refresh, or shortlist MSc programs.
argument-hint: <Canada | Germany | "Ontario Canada" | Europe | USA | all> [--refresh] [--target N]
---

# /find-schools $ARGUMENTS

Run the pipeline below for the location in the arguments. Follow `CLAUDE.md` throughout: accredited
institutions only, official sources only, every fact has a URL, `UNKNOWN` over guessing. Never invent
tuition, deadlines, requirements or program information.

**The VERIFIED rule:** never set `verified` = `YES` (and never treat a fact as verified) unless
`school-verifier` found an official **university** source for that program, meaning it returned
`university_source_found: true`. Everything else stays `verified` = `NO`.

Keep each agent's raw JSON output in the scratchpad (the verifier needs the checker's per-claim
sources). All tracker writes go through `python3 scripts/tracker.py upsert <file>` (active programs)
or `python3 scripts/tracker.py reject <file>` (rejected programs), using JSON files in the scratchpad.

---

## Step 0: Parse the location
Parse the arguments (quotes optional, case-insensitive, commas optional) into a list of
`(country, province_state or none)` targets:
- **Country:** `Canada`, `Germany`, `Ireland`, `USA` / `United States` → the whole country.
- **Province/state + country:** `"Ontario Canada"`, `"Ontario, Canada"`, `"Bavaria Germany"`,
  `"California USA"` → that province/state only. A province/state alone (`Ontario`) is fine if it's
  unambiguous; otherwise ask.
- **Region:** `Europe` → Ireland, Netherlands, Germany, Sweden, Denmark, Finland, Norway, Belgium,
  Switzerland, Austria, France, Italy, Spain, Portugal, Poland, Czechia, Estonia, plus the United
  Kingdom if not excluded. `Nordics` → Sweden, Norway, Denmark, Finland, Iceland.
- **`all`** → Canada, then Europe, then USA, as separate passes in priority order.
- If the location can't be resolved confidently, **ask the user** instead of guessing.

Options:
- `--target N`: the number of new candidates to aim for (default **20** per location; for a region,
  20 per country).
- `--refresh`: re-check every existing row in scope, not just stale ones.

The location slug for file names is the lowercased, hyphenated location, e.g. `canada`, `germany`,
`ontario-canada`, `europe`.

## Step 1: Read `profile.md`
If any core value is missing entirely (nationality, degree field, grade/class, English test status,
target subjects, or maximum tuition), stop and ask the user. Inline `TODO` refinements (exact CGPA,
university name, etc.) don't block the run; list them as limitations in the report. Drop countries
that `profile.md` excludes.

## Step 2: Read `criteria.md`
Re-read it every run, since the user may change filters, points or thresholds. Pass nothing from it
to the researcher; the checker reads it itself.

## Step 3: Check the tracker to avoid duplicate research
1. Run `python3 scripts/tracker.py validate` and fix structural errors (stale rows are fine).
2. Run `python3 scripts/tracker.py list --country "<Country>" [--province "<Province>"]` for each
   target. This lists `schools.csv` **and** `rejected.csv`.
3. Build the **skip list**: every id already in the tracker. These won't be researched again.
4. Build the **refresh queue** of existing `schools.csv` rows that are stale (`--stale 90`), have
   `UNKNOWN`/`CONFLICT` key fields, or all rows in scope with `--refresh`. Rejected rows are only
   re-queued if the reason may have changed (e.g. a new intake year).

## Step 4: Delegate discovery to `school-researcher`
Launch one `school-researcher` subagent per target, in parallel (up to ~4 at a time). For a large
country with no province given (Canada, USA, Germany), you may split it into one agent per
province/state group. Give each:
- its country and province/state
- the skip list for its scope
- its share of the target (step 5)

The researcher finds programs and must not judge eligibility. If it discards a program for an
admissions reason (CS degree, GPA, GRE, English, tuition, deadline), ignore that discard and treat the
program as a candidate. Hold its other discards for reason-only verification (step 7).

## Step 5: Target at least 20 candidate programs
Count the new candidates, excluding skip-list ids and duplicates across agents. If there are fewer than
the target (default 20), run another researcher round on the gaps: institutions not yet searched,
other faculties, more title variants. Never go outside the requested location. For `"Ontario
Canada"`, a shortfall is reported, not filled from other provinces. Stop once the target is reached
or the location is genuinely exhausted. Never pad the list with
off-field programs. If it ends below target, say how many exist and why in the report.

Upsert all candidates with `verified` = `NO` and `stage` = `researching`, mapping `curriculum_hint` →
`key_courses` and `why` → `notes`.

## Step 6: Send candidates to `admission-checker` (investigate mode)
Every new candidate, plus the refresh queue, is promising. Launch `admission-checker` subagents with
the instruction "Mode: investigate", in parallel, batching ~3–5 programs per agent (group by
university). Order the work so programs with **open or unknown deadlines go first**.

Flatten each result's `claims` to values and upsert them with the provisional `eligibility` and
`eligibility_notes`, `stage` = `checked`, `verified` = `NO`. Then split the results:
- **Qualifying:** provisional `eligible` or `borderline` → step 7, full verification.
- **Not qualifying:** provisional `ineligible`, which comes with a `reject_basis` → step 7, reason-only check.

## Step 7: Send candidates to `school-verifier`
Launch `school-verifier` subagents in parallel, ~3–5 programs per agent, grouped by university. Give each:
- **Full verification:** the qualifying candidates, each with the researcher record and the checker's raw `claims`.
- **Reason-only checks:** the `reject_basis` entries for non-qualifying candidates, plus researcher
  discards for the same universities.

Apply the results:
- **Full verification:** upsert `fields`, `conflicts`, `source_urls`, `last_checked`, `confidence`
  and `notes`, with `stage` = `verified`. Set `verified` = `YES` **only if**
  `university_source_found` is `true`; otherwise keep `verified` = `NO` and add "no official
  university source found" to `notes`. Fields the verifier returns as `UNKNOWN` overwrite the
  checker's claims. Never keep an unverified claim as a field value.
- **Full verification found a hard-filter failure** (`currently_offered` = `no`, accreditation
  failed): treat it like a confirmed reason (step 10).
- **Reason confirmed** (`confirmed: true`): step 10.
- **Reason not confirmed:** the program isn't rejected. Send it through full verification in this same run.

Spot-check: for ~1 in 5 verified programs, open one cited university page yourself and confirm the
tuition or deadline appears there. If it doesn't, set `confidence` = `low`, note it, and re-verify.

## Step 8: Score verified candidates
Send every program with `verified` = `YES` from this run to `admission-checker` with the instruction
"Mode: evaluate, no web access" (~10 programs per agent). Programs still at `verified` = `NO` are not
scored. They stay in `schools.csv` without a status and are listed in the report as "Unverified".

Sanity-check the background rule: for any `reject_filter` = `background`, confirm that
`experience_pathway` and `non_cs_eligible` are both `no`. If not, send it back for re-evaluation.

## Step 9: Update `schools.csv`
Upsert every `scored` result (STRONG MATCH / POSSIBLE MATCH) with `stage` = `evaluated`. Never touch
`application_status`; the script also protects it. Run `python3 scripts/tracker.py validate` and fix
anything it reports.

## Step 10: Put unsuitable candidates in `rejected.csv`
Run `python3 scripts/tracker.py reject <file>` for:
- the evaluate-mode `rejected` results (hard-filter fails and low scores)
- confirmed reasons from step 7 (researcher discards and checker `reject_basis`)

Each entry needs `id`, `reject_filter`, a one-line `reason`, `source_url` (the official page the
verifier read), `verified` = `YES` and `last_checked` = today. For researcher discards that were never
in `schools.csv`, also include `country`, `province_state`, `university`, `program` and `program_url`.
The script moves the row out of `schools.csv`, and refuses if the user has set an
`application_status`. In that case, ask the user.

**Passed deadlines are not a rejection** (see `criteria.md`). Those programs stay in `schools.csv`,
marked "DEADLINE PASSED", and rank below open ones.

## Step 11: Produce `reports/<location>.md`
Build it from the tracker for this location, using the ranking order in `criteria.md` (open or unknown
deadlines first, then STRONG before POSSIBLE, then score, then region). It contains:
1. **Header:** date, location, counts (candidates found / checked / verified / strong / possible /
   rejected / unverified), whether the 20-candidate target was met, and profile gaps.
2. **Top 10:** see step 12.
3. **STRONG MATCH table, then POSSIBLE MATCH table**, in ranking order: Rank · University ·
   Province/State · Program · Category · Score · Tuition · App fee · Deadline · Duration · Bachelor
   field · Work exp. considered · IELTS · TOEFL · GRE/GMAT. Link the program name to `program_url`.
   Show `UNKNOWN`/`CONFLICT` as-is, and put one line from `eligibility_notes` under each program.
4. **Score breakdown:** the 9 `pts_*` components for each match.
5. **Upcoming deadlines:** next 90 days, soonest first.
6. **Possible → strong:** what would change it (the `UNKNOWN`s to check, or the gaps to close).
7. **CONFLICTS:** each conflicting field with both values and both source links.
8. **Deadline passed:** these programs are kept for the next intake, ranked last.
9. **Unverified:** programs without an official university source (not scored), and `confidence` = `low` rows.
10. **Rejected this run:** one line each, with the filter and reason.

Also regenerate `reports/shortlist.md` across **all** locations in the tracker: every STRONG and
POSSIBLE MATCH in ranking order, a combined deadline calendar, and an "In progress" section at the top
for programs with an `application_status`.

Append a run entry to `data/research-log.md`:
```
## YYYY-MM-DD — /find-schools <args>
- Location: … · Target: 20 · New candidates: N (target met: yes/no)
- Checked: N · Verified: N · Unverified: N · Strong: N · Possible: N · Rejected: N (by filter)
- Verifier: claims confirmed N · changed N · unconfirmed→UNKNOWN N · CONFLICT N · reasons confirmed N / overturned N
- Exchange rates used: 1 EUR = x CAD (source, date) …
- Issues: unreachable pages, profile gaps
```

## Step 12: Produce a ranked Top 10 summary
The top 10 STRONG/POSSIBLE MATCH programs for this location in `criteria.md` ranking order (open or
unknown deadlines first). Programs whose deadline has passed only appear if fewer than 10 open ones
exist, and are flagged. For each:

`#. University — Program (Province/State) · STATUS · score/100 · deadline · tuition · one-line why`

Put the Top 10 at the top of `reports/<location>.md` **and** in the reply to the user. The reply also
gives:
- counts
- the nearest deadlines
- any CONFLICTs
- whether the 20-candidate target was met
- anything that needs the user's input
- a link to the report

Don't paste the full report.
