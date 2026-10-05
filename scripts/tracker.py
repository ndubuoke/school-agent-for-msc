#!/usr/bin/env python3
"""Safe read/write access to the school tracker.

Active programs live in two CSVs joined on `id`:
  data/schools.csv          the main table (the user's 27 columns, plus id): STRONG / POSSIBLE MATCH
  data/school-details.csv   everything else the agents need (scoring breakdown, sources, conflicts, ...)
Unsuitable programs live in data/rejected.csv.

Callers never need to know which file a column lives in: pass flat objects, get flat objects back.

Usage:
  tracker.py upsert <json-file-or-'-'>          # insert or update active programs (list or single object)
  tracker.py reject <json-file-or-'-'>          # move programs to rejected.csv (removes them from schools)
  tracker.py get <id>                           # print one program as JSON (active or rejected)
  tracker.py list [--country Canada] [--province Ontario] [--stale DAYS]
  tracker.py validate                           # check both CSVs against the schema
  tracker.py schema                             # print columns and allowed values
"""
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# The user's schema (Phase 6), in the user's order, plus a stable id.
MAIN_COLUMNS = [
    "id",
    "country", "province_state", "university", "program", "degree", "category",
    "program_url", "international_url", "duration", "intake", "deadline",
    "tuition_currency", "tuition_amount", "application_fee",
    "bachelor_required", "bachelor_field", "min_gpa", "work_experience_considered",
    "ielts", "toefl", "gre_gmat", "international_students",
    "score", "status", "verified", "last_checked", "notes",
]
DETAIL_COLUMNS = [
    "id",
    # Program
    "region", "city", "faculty", "accreditation", "currently_offered", "program_type",
    "delivery_mode", "language", "coop_internship", "curriculum_focus", "cloud_content",
    "key_courses",
    # Cost
    "tuition_intl_per_year", "tuition_total_cad", "funding",
    # Admissions detail
    "non_cs_eligible", "experience_pathway", "non_cs_notes", "prerequisites",
    "english_waiver", "english_req", "work_experience", "other_requirements",
    # Outcomes
    "post_study_work",
    # Evaluation (admission-checker)
    "eligibility", "eligibility_notes",
    "pts_relevance", "pts_academic", "pts_experience", "pts_tuition", "pts_career",
    "pts_reputation", "pts_international", "pts_structure", "pts_access",
    "best_case_score", "reject_filter",
    # Tracking
    "stage", "application_status", "source_urls", "discovered_via", "confidence", "conflicts",
]
REJECTED_COLUMNS = [
    "id", "country", "province_state", "university", "program", "program_url",
    "reject_filter", "reason", "verified", "source_url", "last_checked",
]
TABLES = {
    "schools": (DATA / "schools.csv", MAIN_COLUMNS),
    "details": (DATA / "school-details.csv", DETAIL_COLUMNS),
    "rejected": (DATA / "rejected.csv", REJECTED_COLUMNS),
}
ALL_COLUMNS = MAIN_COLUMNS + DETAIL_COLUMNS[1:]

ENUMS = {
    # schools.csv
    "category": {"information-systems", "it-management", "cloud-devops", "systems-infrastructure",
                 "applied-computing", "information-security", "technology-management",
                 "digital-transformation", ""},
    "work_experience_considered": {"YES", "NO", "CASE-BY-CASE", "UNKNOWN", ""},
    "gre_gmat": {"REQUIRED", "OPTIONAL", "NOT REQUIRED", "WAIVABLE", "UNKNOWN", ""},
    "international_students": {"YES", "NO", "UNKNOWN", ""},
    "status": {"STRONG MATCH", "POSSIBLE MATCH", ""},
    "verified": {"YES", "NO", ""},
    # school-details.csv
    "region": {"canada", "europe", "usa", ""},
    "currently_offered": {"yes", "no", "UNKNOWN", ""},
    "program_type": {"thesis", "course", "both", "UNKNOWN", ""},
    "delivery_mode": {"on-campus", "online", "hybrid", "UNKNOWN", ""},
    "curriculum_focus": {"technical", "balanced", "management", "UNKNOWN", ""},
    "cloud_content": {"core", "elective", "minimal", "none", "UNKNOWN", ""},
    "non_cs_eligible": {"yes", "case-by-case", "with-bridging", "no", "UNKNOWN", ""},
    "experience_pathway": {"yes", "case-by-case", "no", "UNKNOWN", ""},
    "english_waiver": {"yes", "no", "UNKNOWN", ""},
    "work_experience": {"required", "preferred", "considered", "not-considered", "UNKNOWN", ""},
    "eligibility": {"eligible", "borderline", "ineligible", ""},
    "reject_filter": {"accreditation", "not-offered", "degree-level", "field", "language",
                      "international", "background", "cost", "low-score", "other", ""},
    "stage": {"researching", "checked", "verified", "evaluated", ""},
    "application_status": {"applying", "submitted", "admitted", "rejected-by-school", "declined", ""},
    "confidence": {"high", "medium", "low", ""},
}
# Fact fields where official sources can disagree; school-verifier may set these to CONFLICT.
FACT_ENUMS = {"work_experience_considered", "gre_gmat", "international_students",
              "currently_offered", "program_type", "delivery_mode", "curriculum_focus",
              "cloud_content", "non_cs_eligible", "experience_pathway", "english_waiver",
              "work_experience"}
for _c in FACT_ENUMS:
    ENUMS[_c] = ENUMS[_c] | {"CONFLICT"}

# Max points per scoring component (criteria.md); score must equal their sum.
POINTS = {
    "pts_relevance": 20, "pts_academic": 20, "pts_experience": 15, "pts_tuition": 15,
    "pts_career": 10, "pts_reputation": 5, "pts_international": 5, "pts_structure": 5,
    "pts_access": 5,
}
# The user owns application_status; research runs never change it.
USER_OWNED = {"application_status"}
ID_RE = re.compile(r"^[a-z]{2}-[a-z0-9-]+$")
STALE_DAYS = 90


def read(table):
    path, _ = TABLES[table]
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(table, rows):
    path, cols = TABLES[table]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["id"]):
            w.writerow({c: r.get(c, "") for c in cols})


def read_merged():
    details = {r["id"]: r for r in read("details")}
    return {r["id"]: {**{c: "" for c in ALL_COLUMNS}, **details.get(r["id"], {}), **r}
            for r in read("schools")}


def normalize(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    return str(value).strip()


def upsert(payload):
    items = payload if isinstance(payload, list) else [payload]
    rows = read_merged()
    added, updated = [], []
    for item in items:
        unknown = set(item) - set(ALL_COLUMNS)
        if unknown:
            sys.exit(f"error: unknown columns: {sorted(unknown)}")
        rid = normalize(item.get("id"))
        if not ID_RE.match(rid):
            sys.exit(f"error: bad id {rid!r} (expected e.g. ca-uwindsor-mac)")
        new = {k: normalize(v) for k, v in item.items()}
        for col, val in new.items():
            if col in ENUMS and val not in ENUMS[col]:
                sys.exit(f"error: {rid}: {col}={val!r} not in {sorted(ENUMS[col] - {''})}")
        if rid in rows:
            for col in USER_OWNED:
                if rows[rid][col]:
                    new.pop(col, None)
            rows[rid].update(new)
            updated.append(rid)
        else:
            rows[rid] = {**{c: "" for c in ALL_COLUMNS}, **new}
            added.append(rid)
    write("schools", rows.values())
    write("details", rows.values())
    rejected = read("rejected")
    revived = [x["id"] for x in rejected if x["id"] in rows]
    if revived:
        write("rejected", [x for x in rejected if x["id"] not in rows])
    print(json.dumps({"added": added, "updated": updated, "removed_from_rejected": revived}, indent=2))


def reject(payload):
    items = payload if isinstance(payload, list) else [payload]
    active = read_merged()
    rejected = {x["id"]: x for x in read("rejected")}
    moved = []
    for item in items:
        unknown = set(item) - set(REJECTED_COLUMNS)
        if unknown:
            sys.exit(f"error: unknown columns for rejected.csv: {sorted(unknown)}")
        rid = normalize(item.get("id"))
        if not ID_RE.match(rid):
            sys.exit(f"error: bad id {rid!r}")
        new = {k: normalize(v) for k, v in item.items()}
        for col, val in new.items():
            if col in ENUMS and val not in ENUMS[col]:
                sys.exit(f"error: {rid}: {col}={val!r} not in {sorted(ENUMS[col] - {''})}")
        if not new.get("reject_filter") or not new.get("reason"):
            sys.exit(f"error: {rid}: reject needs reject_filter and reason")
        if rid in active and active[rid]["application_status"]:
            sys.exit(f"error: {rid}: has application_status={active[rid]['application_status']!r}; "
                     "the user owns it, so it can't be auto-rejected. Ask the user.")
        base = {c: active[rid].get(c, "") for c in REJECTED_COLUMNS} if rid in active else {}
        rejected[rid] = {**{c: "" for c in REJECTED_COLUMNS}, **rejected.get(rid, {}), **base, **new}
        active.pop(rid, None)
        moved.append(rid)
    write("rejected", rejected.values())
    write("schools", active.values())
    write("details", active.values())
    print(json.dumps({"rejected": moved}, indent=2))


def age_days(d):
    return (date.today() - datetime.strptime(d, "%Y-%m-%d").date()).days


def validate():
    problems = []
    for table, (path, cols) in TABLES.items():
        if not path.exists():
            problems.append(f"{path.name}: missing")
            continue
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            if next(reader, []) != cols:
                problems.append(f"{path.name}: header does not match schema")
            for n, raw in enumerate(reader, start=2):
                if len(raw) != len(cols):
                    problems.append(f"{path.name}:{n}: {len(raw)} fields, expected {len(cols)}")
        ids = [r["id"] for r in read(table)]
        for rid in {i for i in ids if ids.count(i) > 1}:
            problems.append(f"{path.name}: duplicate id {rid}")
    main_ids = {r["id"] for r in read("schools")}
    detail_ids = {r["id"] for r in read("details")}
    for rid in main_ids ^ detail_ids:
        problems.append(f"{rid}: present in only one of schools.csv / school-details.csv")
    for x in read("rejected"):
        p = lambda msg, rid=x["id"]: problems.append(f"rejected.csv: {rid}: {msg}")
        if x["id"] in main_ids:
            p("also present in schools.csv")
        if not ID_RE.match(x["id"]):
            p("bad id")
        for col in ("reject_filter", "verified"):
            if x[col] not in ENUMS[col]:
                p(f"{col}={x[col]!r} not allowed")
        if not x["reason"]:
            p("no reason")
        if x["verified"] == "YES" and not x["source_url"]:
            p("verified YES but no source_url")

    for rid, r in read_merged().items():
        p = lambda msg: problems.append(f"{rid}: {msg}")
        if not ID_RE.match(rid):
            p("bad id")
        for col, allowed in ENUMS.items():
            if r[col] not in allowed:
                p(f"{col}={r[col]!r} not in {sorted(allowed - {''})}")
        if "CONFLICT" in r.values() and not r["conflicts"]:
            p("has CONFLICT values but empty conflicts column")

        try:
            pts = {c: float(r[c]) for c in POINTS if r[c] != ""}
            score = float(r["score"]) if r["score"] else None
            best = float(r["best_case_score"]) if r["best_case_score"] else score
        except ValueError:
            p("non-numeric score or points")
            continue
        for c, v in pts.items():
            if not 0 <= v <= POINTS[c]:
                p(f"{c}={v:g} outside 0-{POINTS[c]}")
        if score is not None and not 0 <= score <= 100:
            p(f"score {score:g} not 0-100")
        if len(pts) == len(POINTS) and score is not None and abs(sum(pts.values()) - score) > 0.05:
            p(f"score {score:g} != sum of components {sum(pts.values()):g}")

        status = r["status"]
        if status and r["verified"] != "YES":
            p(f"status {status} set before verification (verified={r['verified'] or 'blank'})")
        if r["reject_filter"]:
            p(f"has reject_filter={r['reject_filter']!r} but is still in schools.csv (use `reject`)")
        if status and score is not None:
            want = "STRONG MATCH" if score >= 80 else "POSSIBLE MATCH"
            if score < 65 and (best is None or best < 65):
                p(f"score {score:g} should be REJECT (move to rejected.csv)")
            elif score >= 65 and status != want:
                p(f"score {score:g} should be {want}")

        if r["verified"] == "YES":
            if not r["source_urls"]:
                p("verified YES but no source_urls")
            if not r["last_checked"]:
                p("verified YES but no last_checked")
        if r["last_checked"]:
            try:
                age = age_days(r["last_checked"])
                if age > STALE_DAYS:
                    p(f"stale ({age} days since last_checked)")
            except ValueError:
                p(f"last_checked {r['last_checked']!r} not YYYY-MM-DD")
    print("\n".join(problems) if problems else "ok")
    return 1 if any("stale" not in x for x in problems) else 0


def arg(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd = argv[0]
    if cmd in ("upsert", "reject") and len(argv) == 2:
        src = sys.stdin.read() if argv[1] == "-" else Path(argv[1]).read_text(encoding="utf-8")
        (upsert if cmd == "upsert" else reject)(json.loads(src))
    elif cmd == "get" and len(argv) == 2:
        row = read_merged().get(argv[1])
        if not row:
            row = next(({"table": "rejected", **x} for x in read("rejected") if x["id"] == argv[1]), None)
        if not row:
            sys.exit(f"not found: {argv[1]}")
        print(json.dumps(row, indent=2))
    elif cmd == "list":
        country, province = arg(argv, "--country"), arg(argv, "--province")
        stale = arg(argv, "--stale")
        for rid, r in read_merged().items():
            if country and r["country"].lower() != country.lower():
                continue
            if province and r["province_state"].lower() != province.lower():
                continue
            if stale is not None and r["last_checked"] and age_days(r["last_checked"]) <= int(stale):
                continue
            print("\t".join([rid, r["score"] or "-", r["status"] or "-", f"verified={r['verified'] or '-'}",
                             r["last_checked"] or "-"]))
        if stale is None:
            for x in read("rejected"):
                if country and x["country"].lower() != country.lower():
                    continue
                if province and x["province_state"].lower() != province.lower():
                    continue
                print("\t".join([x["id"], "-", "REJECTED", f"verified={x['verified'] or '-'}",
                                 x["last_checked"] or "-", x["reject_filter"]]))
    elif cmd == "validate":
        return validate()
    elif cmd == "schema":
        for table, (path, cols) in TABLES.items():
            print(f"{path.name}:")
            for c in cols:
                allowed = ENUMS.get(c)
                print(f"  {c}" + (f"  [{', '.join(sorted(allowed - {''}))}]" if allowed else ""))
    else:
        sys.exit(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
