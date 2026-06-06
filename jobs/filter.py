#!/usr/bin/env python3
"""
H-1B Job Filter for Amdadul Haque's profile.

Fetches daily H-1B job repos, parses markdown tables, filters by profile keywords,
and restricts to US-only results by default.

Usage:
    python jobs/filter.py                    # US-only (default)
    python jobs/filter.py --all-countries    # include Europe/global
    python jobs/filter.py --min-score 3
    python jobs/filter.py --verbose
    python jobs/filter.py --output out.json
"""

import re
import json
import argparse
import urllib.request
from datetime import date

SOURCES = [
    {
        "id": "jobright_h1b",
        "name": "Jobright AI — Daily H1B Tech Jobs (US)",
        "url": "https://raw.githubusercontent.com/jobright-ai/Daily-H1B-Jobs-In-Tech/master/README.md",
        "us_only_source": True,   # US-focused repo — skip location filter
    },
    {
        "id": "lamiiine_visa",
        "name": "Lamiiine — Awesome Daily Visa-Sponsored Jobs",
        "url": "https://raw.githubusercontent.com/Lamiiine/Awesome-daily-list-of-visa-sponsored-jobs/main/README.md",
        "us_only_source": False,  # global — apply US location filter
    },
    {
        "id": "speedyapply_ai",
        "name": "Speedyapply — 2026 AI/ML Jobs (US)",
        "url": "https://raw.githubusercontent.com/speedyapply/2026-AI-College-Jobs/main/README.md",
        "us_only_source": True,
    },
]

# ── US detection ──────────────────────────────────────────────────────────────

US_FLAG = "\U0001f1fa\U0001f1f8"  # 🇺🇸
US_LOCATION_KEYWORDS = [
    "usa", "united states", "u.s.", "u.s.a",
    "new york", "san francisco", "los angeles", "chicago", "boston",
    "seattle", "austin", "dallas", "houston", "atlanta", "denver",
    "washington dc", "washington, dc", "san diego", "portland", "miami",
    "minneapolis", "philadelphia", "phoenix", "nashville", "charlotte",
    "raleigh", "salt lake city", "san jose", "remote, usa", "remote (usa)",
    "remote (us)", "us remote", "remote us", ", ny", ", ca", ", tx",
    ", wa", ", ma", ", il", ", ga", ", co", ", fl", ", pa",
]
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
}

def is_us_job(row: dict) -> bool:
    text = " ".join(str(v) for v in row.values())
    if US_FLAG in text:
        return True
    text_lower = text.lower()
    for kw in US_LOCATION_KEYWORDS:
        if kw in text_lower:
            return True
    location = str(row.get("location", "") or "")
    for part in re.split(r"[\s,]+", location):
        if part.upper() in US_STATES:
            return True
    return False

# ── Scoring keywords ──────────────────────────────────────────────────────────
# Format: ([keywords], score_points) — one hit per group

POSITIVE_KEYWORDS = [
    # Seniority
    (["senior", "staff", "principal", "lead", "sr."], 2),
    # Healthcare — top differentiator
    (["healthcare", "health care", "fhir", "hl7", "hipaa", "aidbox",
      "clinical", "medtech", "health tech", "medical", "hospital",
      "patient", "telehealth", "digital health", "health system",
      "health platform", "health data"], 4),
    # Insurance — new domain
    (["insurance", "insurtech", "insurer", "actuarial", "underwriting",
      "claims", "reinsurance", "p&c", "life insurance",
      "health insurance", "insurance platform"], 4),
    # AI / ML / LLM
    (["langgraph", "langchain", "rag", "retrieval-augmented", "llm",
      "multi-agent", "agentic", "mcp", "graphrag",
      "ai engineer", "ml engineer", "mlops", "machine learning",
      "applied researcher", "generative ai", "gen ai",
      "large language model"], 3),
    # Azure / .NET
    (["azure", ".net", "dotnet", "c#", "asp.net"], 2),
    # Cloud / K8s
    (["kubernetes", "aks", "docker", "microservices", "cloud native"], 1),
    # Software Engineer (broad)
    (["software engineer", "software developer", "backend engineer",
      "full stack", "fullstack", "full-stack", "systems engineer"], 1),
    # Python / Data
    (["python", "data science", "data engineer", "data platform"], 1),
    # H-1B / visa
    (["h-1b", "h1b", "visa sponsorship", "sponsorship available",
      "will sponsor", "transfer"], 1),
]

EXCLUDE_KEYWORDS = [
    "us citizen",
    "us citizenship",
    "citizen only",
    "must be a citizen",
    "security clearance",
    "clearance required",
    "top secret",
    "secret clearance",
    "no visa",
    "no sponsorship",
    "not able to sponsor",
    "cannot sponsor",
    "new grad only",
    "entry level only",
    "0-2 years",
    "co-op",
    "co op",
    "intern ",
    "internship",
]

MIN_SCORE = 2

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_markdown(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "job-filter/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("latin-1", errors="replace")
    except Exception as exc:
        print(f"  [warn] Could not fetch {url}: {exc}")
        return ""

# ── Parse markdown tables ─────────────────────────────────────────────────────

def parse_table_rows(markdown: str) -> list[dict]:
    rows = []
    in_table = False
    headers: list[str] = []

    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("|") and line.count("|") >= 3 and not in_table:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 2:
                headers = [re.sub(r"[^a-z0-9_]", "_", h.lower().strip()) for h in cols]
                in_table = True
            continue
        if in_table and re.match(r"^\|[\s\-:|]+\|", line):
            continue
        if in_table and line.startswith("|"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) == len(headers):
                row = {}
                extracted_link = ""
                for k, v in zip(headers, cols):
                    # Capture URLs from markdown links before stripping them
                    if not extracted_link:
                        md_links = re.findall(r'\[[^\]]*\]\((https?://[^)]+)\)', v)
                        if md_links:
                            extracted_link = md_links[0]
                    val = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", v)
                    val = re.sub(r"<[^>]+>", "", val)
                    val = re.sub(r"\*+", "", val)   # strip **bold** markers
                    val = re.sub(r"_{2,}", "", val)  # strip __bold__ markers
                    row[k] = val.strip()
                if extracted_link:
                    row["_link"] = extracted_link
                rows.append(row)
        elif in_table and not line.startswith("|") and line != "":
            in_table = False
            headers = []

    return rows

# ── Scoring ───────────────────────────────────────────────────────────────────

def score_row(row: dict) -> tuple[int, list[str]]:
    text = " ".join(str(v) for v in row.values()).lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            return -1, [f"EXCLUDED:{kw}"]
    score = 0
    matched = []
    for keyword_group, points in POSITIVE_KEYWORDS:
        for kw in keyword_group:
            if kw in text:
                score += points
                matched.append(kw)
                break
    return score, matched

def find_job_link(row: dict) -> str:
    # Prefer URL captured directly from markdown link syntax
    if row.get("_link"):
        return row["_link"]
    raw = " ".join(str(v) for v in row.values())
    urls = re.findall(r"https?://[^\s\)\]\"'<>]+", raw)
    for url in urls:
        if any(x in url for x in ["job", "career", "apply", "lever",
                                    "greenhouse", "workday", "linkedin", "indeed"]):
            return url
    return urls[0] if urls else ""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="H-1B job filter — US focus")
    parser.add_argument("--output", default="jobs/matched_jobs.json")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE)
    parser.add_argument("--all-countries", action="store_true",
                        help="Include non-US jobs (default: US-only)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    us_only = not args.all_countries
    all_matches = []
    today = date.today().isoformat()

    print(f"\n{'='*64}")
    print(f"  H-1B Job Filter — {today}")
    flag = "US-only" if us_only else "All countries"
    print(f"  Mode: {flag}  |  Min score: {args.min_score}")
    print(f"{'='*64}\n")

    for source in SOURCES:
        print(f"Fetching: {source['name']}")
        md = fetch_markdown(source["url"])
        if not md:
            continue

        rows = parse_table_rows(md)
        print(f"  Parsed {len(rows)} rows")

        skipped_non_us = 0
        source_matches = 0

        for row in rows:
            # US filter for global sources
            if us_only and not source.get("us_only_source"):
                if not is_us_job(row):
                    skipped_non_us += 1
                    continue

            score, keywords = score_row(row)
            if score < args.min_score:
                if args.verbose and score >= 0:
                    print(f"  [low score={score}] {list(row.values())[:3]}")
                continue

            entry = {
                "date_found": today,
                "source": source["name"],
                "source_id": source["id"],
                "score": score,
                "matched_keywords": keywords,
                "link": find_job_link(row),
            }
            entry.update(row)
            all_matches.append(entry)
            source_matches += 1

        if skipped_non_us:
            print(f"  Skipped {skipped_non_us} non-US jobs")
        print(f"  Matched: {source_matches} jobs\n")

    all_matches.sort(key=lambda x: x["score"], reverse=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=2, ensure_ascii=False)

    # ── Summary table ──
    print(f"\n{'='*64}")
    print(f"  TOP MATCHES — {len(all_matches)} total  |  saved to {args.output}")
    print(f"{'='*64}")
    print(f"  {'Sc':<4} {'Company':<22} {'Role':<28} {'Location':<16}")
    print(f"  {'-'*4} {'-'*22} {'-'*28} {'-'*16}")

    for job in all_matches[:30]:
        role  = (job.get("job_title") or job.get("role") or
                 job.get("position") or job.get("title") or "")[:27]
        co    = (job.get("company") or job.get("company_name") or "")[:21]
        loc   = (job.get("location") or "")[:15]
        line = f"  {job['score']:<4} {co:<22} {role:<28} {loc:<16}"
        print(line.encode("ascii", errors="replace").decode("ascii"))

    # Domain breakdown
    us_count = sum(1 for j in all_matches if is_us_job(j))
    hc_count = sum(1 for j in all_matches
                   if any(k in ["healthcare","health care","fhir","hl7","hipaa",
                                "clinical","health data","health system"]
                          for k in j.get("matched_keywords", [])))
    ins_count = sum(1 for j in all_matches
                    if any(k in ["insurance","insurtech","underwriting",
                                 "actuarial","claims"]
                           for k in j.get("matched_keywords", [])))

    print(f"\n  US jobs: {us_count}  |  Healthcare: {hc_count}  |  Insurance: {ins_count}")
    print(f"  Next: paste a job URL in career-ops/ and run /career-ops\n",
          end="", flush=True)


if __name__ == "__main__":
    main()
