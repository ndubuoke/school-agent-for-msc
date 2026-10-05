# MSc School Finder

This repository is **not a software project**. It is a personal graduate-school research and
application-management system. Claude researches postgraduate programs, verifies facts against official
university sources, checks eligibility against `profile.md`, ranks programs using `criteria.md`, and
maintains the tracker in `data/`.

Main entry point: `/find-schools <region or country>` (see `.claude/skills/find-schools/SKILL.md`).

## What we're looking for

MSc or closely related master's-level programs in these fields:

- **Information systems & management:** Management Information Systems, Management Information Science,
  Information Systems, Information Management, Information Technology Management, IT Management,
  Technology Management
- **Cloud & DevOps:** Cloud Computing, Cloud Engineering, Cloud Technologies, DevOps, DevOps Engineering,
  Cloud and DevOps
- **Systems & infrastructure:** Distributed Systems, Computer Systems, Infrastructure Engineering
- **Adjacent:** Applied Computing / Applied Computer Science (professional programs open to career
  changers), Systems Science, and Information Systems Security when it's systems- or infrastructure-oriented
- **Digital Transformation**, only when the curriculum has a strong technical/IT component (systems,
  cloud, data, architecture courses). Mostly-strategy or mostly-marketing "digital business" programs don't count.

Region priority: **1. Canada** → **2. Europe** → **3. United States**.

## Source of truth

| File | Owner | Purpose |
|------|-------|---------|
| `profile.md` | User | Background, scores, budget, preferences. Never edit without asking. |
| `criteria.md` | User | Hard filters, 100-point scoring, STRONG / POSSIBLE / REJECT. Never edit without asking. |
| `data/schools.csv` | Claude | One row per active program, in the user's 27-column format, plus `id`: facts, score, `status` (STRONG MATCH / POSSIBLE MATCH) and `verified`. |
| `data/rejected.csv` | Claude | Unsuitable programs, with `reject_filter`, the reason, and the official page confirming it, so they aren't researched again. |
| `data/school-details.csv` | Claude | Everything else per program, joined on `id`: score breakdown, sources, conflicts, eligibility notes, curriculum, `application_status` (the user's progress). |
| `data/research-log.md` | Claude | Append-only log of each research run. |
| `reports/*.md` | Claude | Human-readable summaries, regenerated from the CSVs. |
| `data/SCHEMA.md` | Claude | What every column means. |

## Research rules (non-negotiable)

1. **Never invent information.** Tuition, deadlines, requirements, durations, intakes and program
   details must never come from memory or inference. If a fact cannot be verified, record `UNKNOWN`.
2. **Legitimate, accredited institutions only.**
   - Canada: a public or provincially authorized degree-granting university (e.g. a Universities Canada
     member, or listed by the provincial ministry).
   - United States: institutionally accredited by an agency recognized by the US Department of Education
     or CHEA (regional accreditors such as HLC, MSCHE, WSCUC, SACSCOC, NECHE, NWCCU).
   - Europe: a state-recognized higher-education institution in its country (national ministry list,
     ENIC-NARIC, or anabin "H+" for Germany).
   Record the evidence in `accreditation`. For-profit or unaccredited institutions are REJECT.
3. **Official sources only for verified facts.** Facts must come from the university's own domain or an
   official government or application portal (OUAC, uni-assist, Studyinfo.fi, Universityadmissions.se,
   IRCC, etc.). Third-party education sites (Mastersportal, Yocket, Leverage Edu, rankings sites,
   forums) may be used **for discovery only**. Anything seen only there stays `UNKNOWN`.
4. **Every fact needs a URL.** Record each page used in `source_urls`.
5. **Confirm the program is currently offered.** It must have a live official program page and be
   open, or about to open, for an upcoming intake. Discontinued or suspended programs are REJECT.
6. **Prefer international-student figures.** Record international tuition, deadlines and English
   requirements. Note when a figure is for a different academic year.
7. **Date-stamp verification.** `last_checked` is the date the official page was actually read
   (YYYY-MM-DD). Entries older than 90 days are stale and must be re-verified before being reported as current.
8. **Flag conflicts.** If official sources disagree, set the field to `CONFLICT` and record both
   values with both source URLs in `conflicts`. Don't pick one.
9. **Unverified isn't verified.** Facts found by `school-researcher` or `admission-checker` are claims.
   Only `school-verifier` makes them verified (status `verified`), and anything it can't confirm becomes `UNKNOWN`.
10. **Never apply, register, pay, or submit anything.** This system researches only.

## Tracker conventions

- Always modify the tracker through `scripts/tracker.py`. It takes flat JSON objects, splits them
  across the CSVs, and handles quoting and validation. Don't hand-edit the CSVs, apart from
  `application_status`, which is the user's. The column lists and allowed values live at the top of
  that script. The tracker is CSV for now and may move to SQLite or Postgres later; keeping all access
  in `tracker.py` makes that a one-file change.
- `id` is a stable slug: `<iso2 country>-<university>-<program>`, lowercased with hyphens, e.g.
  `ca-uwindsor-mac`. `country` is the full English country name (`Canada`, `Germany`) and
  `province_state` the province, state or German Land (`Ontario`, `Bavaria`). Re-running research
  updates the existing row instead of duplicating it.
- `verified` = `YES` only when `school-verifier` found an official **university** source for the
  program. `status` is only set after that, and only to `STRONG MATCH` or `POSSIBLE MATCH`.
- Rejections go to `rejected.csv` via `tracker.py reject`, and only after the verifier confirms the
  deciding fact. Passed deadlines are **not** a rejection; those programs rank lower instead.
- Before researching, check `schools.csv` and `rejected.csv`. Skip rejected programs unless the
  reason may have changed (e.g. a new intake year). Only refresh active rows that are stale or have
  `UNKNOWN`/`CONFLICT` key fields.
- Never change `application_status` (`applying`, `submitted`, `admitted`, `rejected-by-school`,
  `declined`). The user owns it, and the script enforces this.
- Money: `tuition_amount` + `tuition_currency` hold the **total program tuition** for international
  students, in the original currency. `school-details.csv` adds `tuition_intl_per_year` and a converted
  `tuition_total_cad`. Record the exchange rate and date in the research log.
