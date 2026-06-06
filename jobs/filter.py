#!/usr/bin/env python3
"""
H-1B Job Filter for Amdadul Haque's profile.

Fetches the daily H-1B job repos, parses markdown job tables,
and filters matches based on profile keywords.

Usage:
    python jobs/filter.py
    python jobs/filter.py --output jobs/matched_jobs.json
    python jobs/filter.py --min-score 2
"""

import re
import json
import argparse
import urllib.request
from datetime import date

SOURCES = [
    {
        "id": "jobright_h1b",
        "name": "Jobright AI — Daily H1B Tech Jobs",
        "url": "https://raw.githubusercontent.com/jobright-ai/Daily-H1B-Jobs-In-Tech/main/README.md",
    },
    {
        "id": "lamiiine_visa",
        "name": "Lamiiine — Awesome Daily Visa-Sponsored Jobs",
        "url": "https://raw.githubusercontent.com/Lamiiine/Awesome-daily-list-of-visa-sponsored-jobs/main/README.md",
    },
    {
        "id": "speedyapply_ai",
        "name": "Speedyapply — 2026 AI/ML Jobs",
        "url": "https://raw.githubusercontent.com/speedyapply/2026-AI-College-Jobs/main/README.md",
    },
]

# Keywords that add to the match score (each hit = +1)
POSITIVE_KEYWORDS = [
    # Seniority — must have at least one
    (["senior", "staff", "principal", "lead", "sr."], 2),
    # Healthcare domain — core differentiator
    (["healthcare", "health care", "fhir", "hl7", "hipaa", "aidbox", "clinical", "medtech", "health tech"], 3),
    # AI / ML — high value
    (["langgraph", "langchain", "rag", "retrieval-augmented", "llm", "multi-agent", "agentic", "mcp",
      "ai engineer", "ml engineer", "mlops", "machine learning", "applied researcher"], 3),
    # Azure / .NET — strong fit
    (["azure", ".net", "dotnet", "c#", "asp.net", "kubernetes", "aks", "docker"], 2),
    # General AI / cloud
    (["python", "ai", "artificial intelligence", "data science", "cloud", "microservices"], 1),
    # Visa / sponsorship (bonus but not required)
    (["h-1b", "h1b", "visa sponsorship", "sponsorship available", "will sponsor"], 1),
]

# Keywords that disqualify a role immediately
EXCLUDE_KEYWORDS = [
    "us citizen",
    "us citizenship",
    "citizen only",
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
    "intern",
    "internship",
]

# Score threshold — jobs below this are not included
MIN_SCORE = 2


def fetch_markdown(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "job-filter/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"  [warn] Could not fetch {url}: {exc}")
        return ""


def parse_table_rows(markdown: str) -> list[dict]:
    """Extract rows from GitHub-flavored markdown tables."""
    rows = []
    in_table = False
    headers: list[str] = []

    for line in markdown.splitlines():
        line = line.strip()

        # Detect header row (contains | and at least 2 columns)
        if line.startswith("|") and line.count("|") >= 3 and not in_table:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 2:
                headers = [h.lower().replace(" ", "_") for h in cols]
                in_table = True
            continue

        # Skip separator row (---|---|---)
        if in_table and re.match(r"^\|[\s\-:|]+\|", line):
            continue

        # Parse data rows
        if in_table and line.startswith("|"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) == len(headers):
                row = dict(zip(headers, cols))
                # Strip markdown link syntax from all values
                for k, v in row.items():
                    # Extract plain text from [text](url)
                    row[k] = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", v)
                    # Remove leftover HTML tags
                    row[k] = re.sub(r"<[^>]+>", "", row[k]).strip()
                rows.append(row)
        elif in_table and not line.startswith("|") and line != "":
            in_table = False
            headers = []

    return rows


def score_row(row: dict) -> tuple[int, list[str]]:
    """Return (score, matched_keywords) for a table row."""
    text = " ".join(str(v) for v in row.values()).lower()

    # Hard exclusions
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
                break  # Only count each group once

    return score, matched


def find_job_link(row: dict) -> str:
    """Try to extract a job URL from the raw markdown row."""
    raw = " ".join(str(v) for v in row.values())
    urls = re.findall(r"https?://[^\s\)\]\"']+", raw)
    return urls[0] if urls else ""


def main():
    parser = argparse.ArgumentParser(description="Filter H-1B job repos for Amdadul Haque's profile")
    parser.add_argument("--output", default="jobs/matched_jobs.json", help="Output JSON file path")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE, help="Minimum score to include a job")
    parser.add_argument("--verbose", action="store_true", help="Show all rows including filtered-out ones")
    args = parser.parse_args()

    all_matches = []
    today = date.today().isoformat()

    print(f"\n{'='*60}")
    print(f"  H-1B Job Filter — {today}")
    print(f"{'='*60}\n")

    for source in SOURCES:
        print(f"Fetching: {source['name']}")
        md = fetch_markdown(source["url"])
        if not md:
            continue

        rows = parse_table_rows(md)
        print(f"  Parsed {len(rows)} rows from table(s)")

        source_matches = 0
        for row in rows:
            score, keywords = score_row(row)
            if score < args.min_score:
                if args.verbose and score >= 0:
                    print(f"  [skip score={score}] {list(row.values())[:3]}")
                continue

            # Try to build a readable job entry
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

        print(f"  Matched: {source_matches} jobs\n")

    # Sort by score descending
    all_matches.sort(key=lambda x: x["score"], reverse=True)

    # Write JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=2, ensure_ascii=False)

    # Print summary table
    print(f"\n{'='*60}")
    print(f"  TOP MATCHES ({len(all_matches)} total) — saved to {args.output}")
    print(f"{'='*60}")
    print(f"  {'Score':<6} {'Source':<18} {'Role / Company':<40}")
    print(f"  {'-'*6} {'-'*18} {'-'*40}")

    for job in all_matches[:25]:
        role = (
            job.get("role", "") or
            job.get("position", "") or
            job.get("title", "") or
            job.get("job_title", "") or
            list(job.values())[5] if len(job) > 5 else ""
        )
        company = (
            job.get("company", "") or
            job.get("company_name", "") or
            list(job.values())[6] if len(job) > 6 else ""
        )
        label = f"{role[:25]} @ {company[:14]}" if role or company else str(list(job.values())[4:6])
        print(f"  {job['score']:<6} {job['source_id']:<18} {label:<40}")
        if job.get("link"):
            print(f"  {'':6} {'':18} {job['link'][:60]}")

    print(f"\n  Next step: paste a job URL into Claude Code and run /career-ops\n")


if __name__ == "__main__":
    main()
