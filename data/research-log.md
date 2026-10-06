# Research Log

Append-only. One entry per `/find-schools` run (newest at the bottom).

## 2026-10-06 — /find-schools Malta (INCOMPLETE: stopped at step 5/6, usage limit)
- Location: Malta · Target: 20 · New candidates: 10 (target met: no, gap round not completed)
- Upserted 10 candidates (verified NO, stage researching): 3 University of Malta, 1 MCAST, 3 GBS HE Malta, 2 STC Higher Education, 1 Ascencia Malta
- Researcher discards (12, not yet verified, not in rejected.csv): 8 UM (mostly part-time only, DLT not offered), EHEI and European Forensic Institute (online), LSC Malta and Global College Malta (off-field)
- Checked: 0 · Verified: 0 · Strong: 0 · Possible: 0 · Rejected: 0
- Issues: um.edu.mt course pages are JS-rendered (WebFetch returns "Loading..."); mfhea.mt register returns 403; private institutions' for-profit status unconfirmed (CLAUDE.md rejects for-profit)
- Resume from: gap-round research (AUM, Saint Martin's, Domain Academy, MLI, IDEA, OPIT, GBSB Global, MCAST IT7-14-21, UM ICT hub), then admission-checker investigate on all 10

## 2026-10-06 — /find-schools Canada (INCOMPLETE — stopped at usage limit)
- Location: Canada · Target: 20 · New candidates: 50 (target met: yes)
- Done: research (3 agents), admission-checker investigate (all 50), verifier (all batches; Regina/Winnipeg/Lethbridge and SFU partially, session limits).
- Written: 16 confirmed rejections to rejected.csv.
- NOT yet done: verified fields not written to schools.csv (all rows still verified=NO); evaluate/scoring; reports; Top 10.
- Unresolved reasons: ca-wlu-mcs-online (page unreachable), ca-polymtl-professional-masters (bot-blocked), ca-concordia-mapcompsc (CS graduate diploma may be a bridging route).
- Unverifiable: ca-brocku-msc-management-ois (brocku.ca blocks automated access).
- Raw agent outputs are in this session's transcript only; a re-run will need to re-verify.
- 2026-10-06 follow-up: added per-agent saving, `data/claims/`, `list --unfinished` and a resume queue to /find-schools. The 43 Canada rows at stage `researching` will resume at step 6 on the next run.

## 2026-10-06 — /find-schools Canada (resumed run, complete)
- Location: Canada · Target: 20 · New candidates: 20 (target met: yes) — Ontario 8, Quebec/Atlantic 6, West 6. Resumed 43 rows from the earlier interrupted run (all at stage `researching` → resumed at step 6).
- Checked: 63 · Verified: 62 · Unverified: 1 (Brock MSc Management OIS — brocku.ca returns 403) · Strong: 0 · Possible: 53 (only 7 score ≥65 on verified facts; 46 are best-case rescues) · Rejected this run: 11 (background 4, field 3, low-score 3, other 1)
- Verifier: changed 194 claims · unconfirmed→UNKNOWN 284 · CONFLICT fields 11 · reasons confirmed 2 (Northeastern Align online-only; UNFC MCS AI field) / overturned 1 (UBC MEng ECE background — calendar allows experience to offset academic deficiency)
- Judgment calls: Concordia Cybersecurity Eng MEng/MASc and ISS MEng/MASc rejected on background (Eng/CS degree only; calendar "deficiency/qualifying" wording judged to cover in-field applicants only). SMU MTEI and Carleton MDTE rejected on field (business/entrepreneurship curricula with no IT/systems content).
- Spot-checks by orchestrator (official pages, 2026-10-06): SMU CDA tuition/deadline ✓, Bishop's deadline/fee ✓, York MAIST intl deadline ✓, Ontario Tech MITS per-credit rate ✓, Concordia BATM tuition/deadline ✓, SFU Cybersecurity tuition/deadline ✓, Northeastern Toronto MPS — page shows 2025-26 figure (50.2K) vs tracker's 2026-27 estimate (50,466); noted on the row.
- Exchange rates used: none (all figures in CAD).
- Fix applied: a verifier wrote UNKNOWN over Brock's identity fields (program, province, URL); restored from git and guarded the save step.
- Issues: most universities haven't published 2027-28 tuition (2026-27 figures used, confidence medium); many deadlines printed without a year (year inferred); uwinnipeg.ca, brocku.ca, ece.ubc.ca, Sauder and some uOttawa pages block automated access; Concordia ISS and Quality Systems MEng pages 404 (status UNKNOWN).
- Profile gaps limiting accuracy: CGPA, degree title/length, coursework (programming/maths/stats), graduation year, exact experience and certifications.
