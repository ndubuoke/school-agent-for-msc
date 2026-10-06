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
