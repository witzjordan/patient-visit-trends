# Patient Visit Trends — Hospital Attendance Analysis

**By Oru Stanley Enowru — Junior Data Scientist**

> ⚠️ **All data in this project is synthetic** (generated with Python, seed 42).
> No real patient data is used. It is a portfolio project demonstrating
> data cleaning, exploratory analysis and visualisation on hospital-style data.

## What this project does

Takes a messy hospital-visits dataset, cleans it, and answers:
1. How did attendance change month to month?
2. Which department / service was busiest?
3. Is there a weekday pattern?

## Files

| File | What it is |
|---|---|
| `analysis.py` | The full pipeline: generate → clean → analyse → chart. Run with `python3 analysis.py` |
| `data/hospital_visits_raw.csv` | Messy dataset as generated (8,620 rows) |
| `data/hospital_visits_clean.csv` | Cleaned, analysis-ready dataset (8,217 rows) |
| `charts/monthly_attendance.png` | Monthly visits, Jan–Dec 2025 |
| `charts/visits_by_department.png` | Visits by department |
| `results_summary.txt` | Full numbers from the run |

## Key results (from the actual run)

- **8,217 clean visits analysed**, covering **12 months (Jan–Dec 2025)**
- **Busiest month: August 2025 — 839 visits** (10.2% of all visits); quietest was February 2025 — 570 visits. Visits rose through the June–September period (757–839/month) and fell back to ~600 in December.
- **Busiest department: General Medicine — 2,495 visits (30.4%)**, followed by Pediatrics — 1,516 (18.4%) and Emergency — 1,162 (14.1%)
- **Weekday pattern: fairly even.** Saturday was highest at 1,222 visits and Thursday lowest at 1,138 — no strong weekday effect in this dataset.
- **Average wait time: 41.7 minutes**; median patient age 37 years; 48.9% female.

## Cleaning (with counts — this is the point of the project)

The raw data was deliberately messy, as real hospital data is:

| Problem | Count |
|---|---|
| Duplicate rows found and removed | 109 exact duplicates (120 duplicate rows were injected; 11 had missing values added afterwards, so they were no longer exact duplicates) |
| Missing values in the raw data | 414 (4.8% of raw rows): age 179, gender 95, wait time 140 |
| Rows dropped (missing age or gender) | 270 |
| Impossible ages removed (< 0 or > 100) | 24 |
| Inconsistent department spellings standardised | 20 variants → 8 departments (e.g. "general medicine", "GENERAL MEDICINE", "Paediatrics" → "Pediatrics") |
| Missing wait times filled | Department median |

## Tools

Python, pandas, NumPy, Matplotlib.

## How to reproduce

```bash
python3 analysis.py
```

This regenerates the data, re-runs the cleaning and analysis, and
recreates both charts and `results_summary.txt`.
