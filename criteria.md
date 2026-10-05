# Selection Criteria

Every researched program ends up with exactly one classification:

| Classification | Meaning | Where it lives |
|----------------|---------|----------------|
| **STRONG MATCH** | Score 80–100. Apply. | `data/schools.csv`, `status` column |
| **POSSIBLE MATCH** | Score 65–79, or likely to reach 65 once `UNKNOWN`s are resolved (see below). Worth considering. | `data/schools.csv`, `status` column |
| **REJECT** | Fails a hard filter, or scores 0–64. | `data/rejected.csv`, with `reject_filter` and `reason` |

STRONG and POSSIBLE are set only after verification. A REJECT's deciding fact is always confirmed by
`school-verifier` first.

Who does what:
- `school-researcher` only finds programs.
- `admission-checker` investigates requirements, then applies everything in this file.
- `school-verifier` confirms facts on official sources.

---

## Step 1: Hard filters

These are facts about the **program**, not judgments about the applicant. Failing any one means
**REJECT** (with the `reject_filter` value shown), regardless of score.

| # | Filter | Reject when | `reject_filter` |
|---|--------|-------------|----------|
| 1 | Accredited institution | Not a legitimate, accredited or state-recognized university (rules in `CLAUDE.md`) | `accreditation` |
| 2 | Currently offered | Discontinued, suspended, or not admitting for any upcoming intake | `not-offered` |
| 3 | Master's level | Not a master's degree that `profile.md` lists as acceptable (certificates, diplomas and PG certs don't count) | `degree-level` |
| 4 | Field | No meaningful overlap with the primary or adjacent subjects in `profile.md`, judged by curriculum | `field` |
| 5 | Language | Not taught in English | `language` |
| 6 | International | Closed to international or study-permit students | `international` |
| 7 | Delivery | Online-only or part-time-only (no study permit or post-study work) | `other` |
| 8 | Cost ceiling | Verified total tuition is above the **maximum absolute tuition** in `profile.md` | `cost` |
| 9 | Background | **Only** when the program explicitly requires a computing/CS degree **and** offers no alternative pathway (see below) | `background` |

### The non-CS rule (filter 9)
A program must **not** be rejected just because the applicant's bachelor's degree isn't in computing,
if the university offers **any** of these routes:
- professional IT experience can satisfy prerequisites or replace the degree requirement
- "any discipline" or "related discipline" degrees are accepted
- case-by-case or holistic review is mentioned
- bridging, qualifying, pre-master's or foundation courses are available
- admission is conditional on completing prerequisite courses

If the program is silent on non-CS backgrounds, it is **not** a reject. Score it with
`experience_pathway` = `UNKNOWN`, and the report will flag it as "ask the program".

A fact that is `UNKNOWN` never triggers a hard filter on its own.

---

## Step 2: Score (0–100)

Award points for each component, up to its maximum. The total is the score.

| Component | Max | What it measures | Full marks | Zero |
|-----------|----:|------------------|-----------|------|
| **Course relevance** | 20 | Fit with the preferred subjects (in priority order), amount of technical/cloud content, and balance of management and technical courses | Core courses in cloud/DevOps/infrastructure **and** IS/IT management; matches a top-3 preferred subject | Only loosely related, or purely theoretical/maths-heavy |
| **Academic eligibility** | 20 | Non-CS degree acceptance, GPA vs requirement, English requirement, GRE/GMAT | "Any discipline" accepted; 2:1 clearly meets the minimum; English waived for Nigerian degrees; no GRE/GMAT | Needs CS-specific prerequisites the applicant lacks, a GPA at the cutoff, a test with no waiver, and a required GRE |
| **Professional experience** | 15 | Whether IT experience can substitute for academic prerequisites, and whether it is valued in admissions | Explicitly says experience can replace prerequisites or the degree requirement, and the program values or requires experience | Experience not considered, and prerequisites must be academic |
| **Tuition affordability** | 15 | Total tuition **after guaranteed funding**, against the budget in `profile.md`. Non-guaranteed scholarships add up to +2 | ≤ 50% of preferred max | At absolute max (half marks at preferred max) |
| **Career alignment** | 10 | Post-study employment prospects: post-study work route (Canada PGWP, EU job-seeker permit, US STEM OPT), co-op or internship, industry links, fit with the career goal | PGWP-eligible with co-op, strong local tech market | No post-study work route |
| **University reputation** | 5 | Standing in this field (published rankings may be used here only, cited in `notes`) | QS/THE subject top 100 or national top 5 | Little recognition |
| **International eligibility** | 5 | How smoothly an international applicant gets in | Explicitly welcomes international students; study-permit and PGWP eligible (designated learning institution); Nigerian credentials clearly addressed | Open but with restrictions (quotas, a credential evaluation like WES is required, unclear permit eligibility) |
| **Program structure** | 5 | Duration and format | 12–24 months full-time, on-campus | Over 30 months, or an awkward format |
| **Application accessibility** | 5 | Deadline feasibility, application fee, document burden | Deadline ≥ 3 months away; fee ≤ 150 CAD; standard documents | Deadline < 3 weeks away **or already passed**; high fee; heavy extra requirements |
| **Total** | **100** | | | |

### Scoring rules
- Score **only from verified facts** in the tracker and from `profile.md`. Never from assumptions.
- **UNKNOWN components** get **half** their points, and the component is listed in `eligibility_notes`.
- **Best-case rescue:** if a program scores below 65 but would reach 65 or more with every `UNKNOWN`
  scored at full marks, classify it **POSSIBLE MATCH** (not REJECT) and say what needs checking.
- Region priority (Canada → Europe → US) is **not** part of the score.

### Passed deadlines
A program whose international deadlines for the target intake have **all passed** is **not**
rejected, because it may suit the next intake. It is:
- scored normally, with 0 points for application accessibility's deadline part
- labelled **"DEADLINE PASSED"** in `notes`
- **always ranked below** every program with an open deadline (or an `UNKNOWN` deadline)

### Ranking order (reports and Top 10)
1. Programs with an open or `UNKNOWN` deadline before programs whose deadline has passed
2. STRONG MATCH before POSSIBLE MATCH
3. Higher score first
4. Region priority (Canada → Europe → USA) as the tie-breaker

---

## Step 3: Classify

| Score | Classification |
|-------|----------------|
| 80–100 | **STRONG MATCH** |
| 65–79 | **POSSIBLE MATCH** |
| 0–64 | **REJECT** (`reject_filter` = `low-score`, with the score and its two weakest components in `reason`) |

Programs that fail a hard filter are **REJECT** whatever their score.
