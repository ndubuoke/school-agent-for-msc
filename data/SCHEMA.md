# Tracker Schema

Active programs live in two CSVs joined on `id`; unsuitable programs live in `rejected.csv`.
`scripts/tracker.py` is the only writer (`upsert` for active programs, `reject` to move one to
`rejected.csv`), and it enforces this
schema (`python3 scripts/tracker.py schema` lists the allowed values).

- Facts that couldn't be verified on an official source are `UNKNOWN`.
- Facts where official sources disagree are `CONFLICT`, with both values and sources in `conflicts`.
- Multi-value fields use ` | ` as the separator.

Storage is CSV for now. It may move to SQLite or Postgres later; only `tracker.py` would change.

## data/schools.csv — main table

The user's 27 columns, in the user's order, plus a leading `id`.

| Column | Example | Notes |
|--------|---------|-------|
| `id` | `ca-uwindsor-mac` | `<iso2>-<university>-<program>` slug, stable across runs. Used to join the details file |
| `country` | Canada | Full English name |
| `province_state` | Ontario | Province, state, German Land, etc. |
| `university` | University of Windsor | Official name |
| `program` | Master of Applied Computing | Official program name |
| `degree` | MAC | MSc, MS, MASc, MEng, MIS, … |
| `category` | applied-computing | `information-systems` · `it-management` · `cloud-devops` · `systems-infrastructure` · `applied-computing` · `information-security` · `technology-management` · `digital-transformation` |
| `program_url` | https://… | Official program page |
| `international_url` | https://… | Official international-applicant admissions page |
| `duration` | 16 months | Normal full-time length |
| `intake` | Fall \| Winter | Intakes open to international students |
| `deadline` | 2027-02-01 | YYYY-MM-DD, international deadline for the target intake. Rounds separated by ` \| ` |
| `tuition_currency` | CAD | ISO 4217 |
| `tuition_amount` | 54000 | **Total program** tuition, international rate. Calculation in `notes` |
| `application_fee` | 125 CAD | |
| `bachelor_required` | 4-year bachelor's, 70% average | Degree type, length and standing |
| `bachelor_field` | Any discipline; programming course required | Which fields of study are accepted |
| `min_gpa` | B (70%) | As stated by the program |
| `work_experience_considered` | YES | `YES` · `NO` · `CASE-BY-CASE`. Is professional experience considered (in admissions or in place of prerequisites)? |
| `ielts` | 6.5 overall, 6.0 each band | |
| `toefl` | iBT 90, 20 each section | |
| `gre_gmat` | NOT REQUIRED | `REQUIRED` · `OPTIONAL` · `NOT REQUIRED` · `WAIVABLE` |
| `international_students` | YES | Open to international/study-permit students? `YES` · `NO` |
| `score` | 84 | 0–100, the sum of the `pts_*` components in the details file |
| `status` | STRONG MATCH | `STRONG MATCH` · `POSSIBLE MATCH`. Blank until verified and evaluated |
| `verified` | YES | `YES` = `school-verifier` found an official university source and every fact is now a verified value, `UNKNOWN` or `CONFLICT`. `NO` = contains unverified claims, or no university source was found |
| `last_checked` | 2026-10-05 | YYYY-MM-DD the official pages were read. Older than 90 days = stale |
| `notes` | | Calculations, caveats, "DEADLINE PASSED" |

## data/school-details.csv — everything else, by `id`

### Program
| Column | Notes |
|--------|-------|
| `region` | `canada` · `europe` · `usa` |
| `city`, `faculty` | |
| `accreditation` | Evidence the institution is legitimate |
| `currently_offered` | `yes` · `no` · `UNKNOWN` · `CONFLICT` |
| `program_type` | `thesis` · `course` · `both` |
| `delivery_mode` | `on-campus` · `online` · `hybrid` |
| `language` | Language of instruction |
| `coop_internship` | Co-op, internship or industry capstone |
| `curriculum_focus` | `technical` · `balanced` · `management` |
| `cloud_content` | `core` · `elective` · `minimal` · `none` |
| `key_courses` | Core courses that justify the field fit |

### Cost
| Column | Notes |
|--------|-------|
| `tuition_intl_per_year` | International, per year, in `tuition_currency` |
| `tuition_total_cad` | Converted estimate; the rate goes in the research log |
| `funding` | What international students can get |

### Admissions detail
| Column | Notes |
|--------|-------|
| `non_cs_eligible` | `yes` · `case-by-case` · `with-bridging` · `no` |
| `experience_pathway` | Can IT experience **substitute for academic prerequisites**? `yes` · `case-by-case` · `no` |
| `non_cs_notes` | The deciding quotes from official pages |
| `prerequisites` | Required background courses |
| `english_waiver` | Is the test waived for the applicant's (Nigerian, English-medium) degree? `yes` · `no` |
| `english_req` | Other accepted tests (Duolingo, PTE) and the waiver wording |
| `work_experience` | `required` · `preferred` · `considered` · `not-considered` (finer than `work_experience_considered`) |
| `other_requirements` | References (how many, what type), statement of purpose, CV, interview, portfolio |

### Outcomes
| Column | Notes |
|--------|-------|
| `post_study_work` | e.g. "PGWP eligible", from the official government source |

### Evaluation (admission-checker)
| Column | Notes |
|--------|-------|
| `eligibility` | `eligible` · `borderline` · `ineligible` |
| `eligibility_notes` | The specific reasons, in 2–4 sentences |
| `pts_relevance` (20) · `pts_academic` (20) · `pts_experience` (15) · `pts_tuition` (15) · `pts_career` (10) · `pts_reputation` (5) · `pts_international` (5) · `pts_structure` (5) · `pts_access` (5) | Points per `criteria.md` component, 0 up to the max shown |
| `best_case_score` | Score with every `UNKNOWN`/`CONFLICT` component at full marks |

### Tracking
| Column | Notes |
|--------|-------|
| `stage` | Pipeline progress: `researching` → `checked` (requirements found, unverified) → `verified` → `evaluated` |
| `application_status` | **User-owned.** `applying` · `submitted` · `admitted` · `rejected-by-school` · `declined`. The agents never change it |
| `source_urls` | Every official page used |
| `discovered_via` | Where the program was first found (may be third-party; never cited as a source) |
| `confidence` | `high` · `medium` · `low` |
| `conflicts` | `field: 'A' (url) vs 'B' (url)` for each field set to `CONFLICT` |

## data/rejected.csv — unsuitable programs

Written only by `tracker.py reject`, which also removes the program from the two active files.

| Column | Notes |
|--------|-------|
| `id`, `country`, `province_state`, `university`, `program`, `program_url` | As in schools.csv |
| `reject_filter` | `accreditation` · `not-offered` · `degree-level` · `field` · `language` · `international` · `background` · `cost` · `low-score` · `other` |
| `reason` | One line. For `low-score`: the score, best case, and the two weakest components |
| `verified` | `YES` = the verifier confirmed the deciding fact on an official page |
| `source_url` | The official page confirming the reason |
| `last_checked` | YYYY-MM-DD |

A passed deadline is **not** a rejection. Those programs stay in schools.csv and rank lower.
