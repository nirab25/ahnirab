# H-1B Job Search Setup Guide
**For: Amdadul Haque (Nirab) — Senior Software Engineer**

End-to-end workflow using `career-ops` (AI job evaluator) + daily H-1B repo filters + a browser-based tracker.

---

## Overview

```
Daily H1B repos  →  jobs/filter.py  →  matched_jobs.json
                                              ↓
                                 Paste job URL into Claude Code
                                              ↓
                                    /career-ops → A–F score
                                    + tailored CV PDF
                                    + skills gap list
                                              ↓
                                 Import into jobs/dashboard.html
                                              ↓
                                    /career-ops training
                                    → courses for skill gaps
                                    → interview prep per role
```

---

## Step 1 — Fork career-ops

1. Go to https://github.com/santifer/career-ops
2. Click **Fork** → fork to your account as `nirab25/career-ops`
3. Clone it locally:
   ```bash
   git clone https://github.com/nirab25/career-ops.git
   cd career-ops
   ```

---

## Step 2 — Copy your pre-built config into the fork

From this repo (`nirab25/ahnirab`), copy:

```bash
cp career-ops/config/profile.yml  ~/career-ops/config/profile.yml
cp career-ops/cv.md               ~/career-ops/cv.md
cp career-ops/config/portals.yml  ~/career-ops/config/portals.yml
```

---

## Step 3 — Install career-ops

```bash
cd ~/career-ops
npm install
npx playwright install chromium
npm run doctor          # Should show all green
```

---

## Step 4 — Daily job filter

Run from this repo's root each morning:

```bash
python jobs/filter.py
```

This fetches the latest job listings from:
- `jobright-ai/Daily-H1B-Jobs-In-Tech`
- `Lamiiine/Awesome-daily-list-of-visa-sponsored-jobs`
- `speedyapply/2026-AI-College-Jobs`

Filters by your profile keywords and saves matches to `jobs/matched_jobs.json`.

**Optional flags:**
```bash
python jobs/filter.py --min-score 3      # stricter filtering
python jobs/filter.py --verbose          # show all rows
python jobs/filter.py --output out.json  # custom output path
```

---

## Step 5 — Evaluate a job with career-ops

1. Open Claude Code inside your career-ops fork directory
2. Paste a job URL or description
3. Run: `/career-ops`

You'll get:
- **A–F score** across 10 weighted dimensions
- **Tailored CV PDF** (ATS-optimized, reads your `cv.md`)
- **Skills gap list** — what you're missing for this role
- **Tracker entry** logged automatically

> Tip: `/career-ops` will recommend applying to anything scoring **B or above**. Skip F–D unless the company is on your target list.

---

## Step 6 — Track in the dashboard

1. Open `jobs/dashboard.html` in your browser (file:// works — no server needed)
2. To bulk-import filter results:
   - Click **Import JSON** → select `jobs/matched_jobs.json`
   - All new matches are added with status "Wishlist"
3. Update status as you progress: Wishlist → Applied → Phone Screen → Interview → Offer

---

## Step 7 — Skills gap & interview prep

When career-ops identifies a skills gap (e.g., "LangGraph advanced"), run:

```
/career-ops training
```

This recommends courses and certs based on the specific job's requirements vs your profile.

Before each interview, run:

```
/career-ops deep [Company Name]
```

This researches the company, their tech stack, recent news, and generates likely interview questions for your role.

---

## Key Sources Reference

| Source | Best For | Update Frequency |
|--------|----------|-----------------|
| `jobright-ai/Daily-H1B-Jobs-In-Tech` | Verified H-1B sponsors | Daily |
| `Lamiiine/Awesome-daily-list-of-visa-sponsored-jobs` | Senior roles + Europe | Daily |
| `speedyapply/2026-AI-College-Jobs` | AI company names | Daily |
| MyVisaJobs.com | H-1B history by employer | Monthly |
| H1BGrader.com | Employer approval rate | Monthly |
| LinkedIn (saved searches) | Senior/Staff direct posts | Real-time |

**LinkedIn searches pre-configured in `career-ops/config/portals.yml`:**
- Healthcare AI Engineer (Senior, Remote)
- Senior .NET Azure Healthcare
- LangGraph RAG AI Engineer (Senior)
- FHIR HL7 Software Engineer (Senior)
- MLOps Senior/Staff Engineer

---

## Visa Note

You have an **active H-1B** — you're seeking a **transfer**, not a new cap filing.

- Do NOT filter out companies that don't explicitly mention sponsorship
- DO exclude: "US citizenship required", "security clearance required", "no visa sponsorship"
- H-1B transfers are processed under cap-exempt regulations — most companies that have ever sponsored will do it
- Check the employer's H-1B history at https://www.myvisajobs.com before applying

---

## Target Companies (pre-loaded in profile.yml)

| Company | Domain | Why |
|---------|--------|-----|
| Epic Systems | Healthcare EHR | FHIR-heavy, strong H-1B history |
| Tempus AI | Oncology AI | Python/ML + AI fit |
| Oracle Health | Healthcare Cloud | Azure/cloud architecture fit |
| Hippocratic AI | Healthcare LLM | LangChain, multi-agent systems |
| Flatiron Health | Oncology Data | FHIR stack, data engineering |
| Microsoft (Health) | Cloud AI | Azure Health Data Services |
| Google Health | Health AI | Vertex AI + FHIR on GCP |
| Databricks | ML Platform | MLOps, Delta Lake |
| Palantir | Data Analytics | Healthcare contracts, H-1B sponsor |

---

## Files in This Repo

```
career-ops/
  config/
    profile.yml        ← your candidate profile for career-ops
    portals.yml        ← job sources + LinkedIn searches
  cv.md               ← your CV in Markdown (career-ops reads this)

jobs/
  filter.py           ← daily H-1B job filter script
  dashboard.html      ← browser job tracker (open locally, no server)
  matched_jobs.json   ← generated by filter.py

SETUP.md             ← this file
```
