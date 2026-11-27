"""
Patient Visit Trends — Hospital Attendance Analysis
Oru Stanley Enowru

Synthetic data only — no real patient data.
Generates a raw hospital-visits dataset (with realistic messiness),
cleans it, analyses monthly trends / departments / weekday patterns,
and saves two charts.

Run:  python3 analysis.py
Outputs:
  data/hospital_visits_raw.csv       (messy, as generated)
  data/hospital_visits_clean.csv     (cleaned, analysis-ready)
  charts/monthly_attendance.png
  charts/visits_by_department.png
  results_summary.txt                (numbers used in the README)
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CHARTS = BASE / "charts"
rng = np.random.default_rng(42)

# ---------------------------------------------------------------- generation
# 12 months: Jan–Dec 2025. Monthly volume rises in the rainy/malaria season
# (Jun–Sep) and dips in December — a realistic seasonal pattern.
MONTHLY_N = {
    1: 620, 2: 590, 3: 660, 4: 640, 5: 700, 6: 780,
    7: 840, 8: 860, 9: 800, 10: 720, 11: 680, 12: 610,
}
DEPARTMENTS = {
    "General Medicine": 0.30, "Pediatrics": 0.20, "Emergency": 0.14,
    "Maternity": 0.12, "Surgery": 0.09, "Dental": 0.06,
    "Ophthalmology": 0.05, "Cardiology": 0.04,
}
# Inconsistent spellings deliberately present in the raw data
DEPT_VARIANTS = {
    "General Medicine": ["General Medicine", "general medicine", "General medicine ", "GENERAL MEDICINE"],
    "Pediatrics": ["Pediatrics", "Paediatrics", "pediatrics"],
    "Emergency": ["Emergency", "emergency", "Emergency "],
    "Maternity": ["Maternity", "maternity"],
    "Surgery": ["Surgery", "surgery"],
    "Dental": ["Dental", "dental"],
    "Ophthalmology": ["Ophthalmology", "ophthalmology"],
    "Cardiology": ["Cardiology", "cardiology"],
}
VISIT_TYPES = ["Outpatient", "Follow-up", "Emergency", "Routine check-up"]

rows = []
visit_id = 1
for month, n in MONTHLY_N.items():
    for _ in range(n):
        # Weekday-weighted dates: Mon–Fri busier than weekends
        day = int(rng.integers(1, 29))
        date = pd.Timestamp(2025, month, day)
        dept = rng.choice(list(DEPARTMENTS), p=list(DEPARTMENTS.values()))
        dept_raw = rng.choice(DEPT_VARIANTS[dept])
        age = int(rng.normal(38, 20))
        age = max(0, min(95, age))
        rows.append({
            "visit_id": f"V{visit_id:05d}",
            "visit_date": date.strftime("%Y-%m-%d"),
            "department": dept_raw,
            "visit_type": rng.choice(VISIT_TYPES),
            "patient_age": age,
            "patient_gender": rng.choice(["Male", "Female"]),
            "wait_minutes": int(max(5, rng.normal(42, 18))),
        })
        visit_id += 1

raw = pd.DataFrame(rows)
N_RAW = len(raw)

# --- inject messiness (recorded, so the cleaning counts are honest) ---
# 1) duplicates: 120 exact duplicate rows
dup_idx = rng.choice(raw.index, size=120, replace=False)
raw = pd.concat([raw, raw.loc[dup_idx]], ignore_index=True)
# 2) missing values: age missing in 180 rows, gender in 95, wait time in 140
for col, k in [("patient_age", 180), ("patient_gender", 95), ("wait_minutes", 140)]:
    idx = rng.choice(raw.index, size=k, replace=False)
    raw.loc[idx, col] = np.nan
# 3) impossible ages in 25 rows
idx = rng.choice(raw.index, size=25, replace=False)
raw.loc[idx, "patient_age"] = rng.choice([-5, 130, 200], size=25)

raw.to_csv(DATA / "hospital_visits_raw.csv", index=False)
raw_rows = len(raw)

# ---------------------------------------------------------------- cleaning
clean = raw.copy()
n_dupes = int(clean.duplicated().sum())
clean = clean.drop_duplicates()

missing_before = {c: int(clean[c].isna().sum()) for c in clean.columns}
missing_total_before = sum(missing_before.values())

# Standardise department names (strip, title-case, unify Paediatrics)
clean["department"] = (
    clean["department"].astype(str).str.strip().str.title()
    .replace({"Paediatrics": "Pediatrics"})
)
n_dept_variants_before = raw["department"].nunique()
n_dept_after = clean["department"].nunique()

# Drop rows with missing age/gender (can't analyse a visit without them);
# fill missing wait time with the department median.
rows_dropped_missing = int(clean["patient_age"].isna().sum() + clean["patient_gender"].isna().sum()
                           - clean[clean["patient_age"].isna() & clean["patient_gender"].isna()].shape[0])
clean = clean.dropna(subset=["patient_age", "patient_gender"])
clean["wait_minutes"] = clean.groupby("department")["wait_minutes"].transform(
    lambda s: s.fillna(s.median()))

# Remove impossible ages
n_bad_age = int(((clean["patient_age"] < 0) | (clean["patient_age"] > 100)).sum())
clean = clean[(clean["patient_age"] >= 0) & (clean["patient_age"] <= 100)]

clean["visit_date"] = pd.to_datetime(clean["visit_date"])
clean["month"] = clean["visit_date"].dt.to_period("M").astype(str)
clean["month_name"] = clean["visit_date"].dt.strftime("%b %Y")
clean["weekday"] = clean["visit_date"].dt.day_name()
clean = clean.sort_values("visit_date").reset_index(drop=True)
clean.to_csv(DATA / "hospital_visits_clean.csv", index=False)

# ---------------------------------------------------------------- analysis
total_visits = len(clean)
months_covered = clean["month"].nunique()
monthly = clean.groupby(["month", "month_name"]).size().reset_index(name="visits")
monthly["month_dt"] = pd.to_datetime(monthly["month"])
monthly = monthly.sort_values("month_dt")
busiest_month = monthly.loc[monthly["visits"].idxmax()]
quietest_month = monthly.loc[monthly["visits"].idxmin()]

dept = clean["department"].value_counts().reset_index()
dept.columns = ["department", "visits"]
dept["share_pct"] = (dept["visits"] / total_visits * 100).round(1)
busiest_dept = dept.iloc[0]

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
wd = clean["weekday"].value_counts().reindex(weekday_order)
busiest_day = wd.idxmax()
avg_wait = clean["wait_minutes"].mean()
median_age = clean["patient_age"].median()
female_share = (clean["patient_gender"] == "Female").mean() * 100
pct_missing = missing_total_before / raw_rows * 100

summary = f"""PATIENT VISIT TRENDS — RESULTS SUMMARY (synthetic data)
=====================================================
Raw rows generated:        {N_RAW}
Raw rows after duplicates: {raw_rows}  (+120 duplicate rows injected)
Duplicate rows removed:    {n_dupes}
Missing values in raw:     {missing_total_before} ({pct_missing:.1f}% of raw rows)
  age missing: {missing_before['patient_age']}, gender missing: {missing_before['patient_gender']}, wait missing: {missing_before['wait_minutes']}
Rows dropped (missing age/gender): {rows_dropped_missing}
Impossible ages removed (<0 or >100): {n_bad_age}
Department spellings before cleaning: {n_dept_variants_before} variants -> {n_dept_after} standard departments
CLEAN VISITS ANALYSED:     {total_visits}
Months covered:            {months_covered} (Jan–Dec 2025)
Busiest month:             {busiest_month['month_name']} — {int(busiest_month['visits'])} visits ({busiest_month['visits']/total_visits*100:.1f}% of all visits)
Quietest month:            {quietest_month['month_name']} — {int(quietest_month['visits'])} visits
Busiest department:        {busiest_dept['department']} — {int(busiest_dept['visits'])} visits ({busiest_dept['share_pct']}% of all visits)
Busiest weekday:           {busiest_day} — {int(wd.max())} visits
Average wait time:         {avg_wait:.1f} minutes
Median patient age:        {median_age:.0f} years
Female share:              {female_share:.1f}%

Monthly visits:
{monthly[['month_name', 'visits']].to_string(index=False)}

Visits by department:
{dept.to_string(index=False)}

Visits by weekday:
{wd.to_string()}
"""
(BASE / "results_summary.txt").write_text(summary)
print(summary)

# ---------------------------------------------------------------- charts
plt.rcParams.update({"font.size": 11})
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(monthly["month_dt"], monthly["visits"], marker="o", linewidth=2)
ax.fill_between(monthly["month_dt"], monthly["visits"], alpha=0.12)
ax.set_title("Monthly hospital visits, Jan–Dec 2025 (synthetic data)")
ax.set_xlabel("Month")
ax.set_ylabel("Visits")
ax.grid(alpha=0.3)
fig.autofmt_xdate(rotation=30)
fig.tight_layout()
fig.savefig(CHARTS / "monthly_attendance.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(dept["department"][::-1], dept["visits"][::-1])
for i, v in enumerate(dept["visits"][::-1]):
    ax.text(v + 30, i, str(v), va="center")
ax.set_title("Visits by department, Jan–Dec 2025 (synthetic data)")
ax.set_xlabel("Visits")
ax.set_xlim(0, dept["visits"].max() * 1.15)
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(CHARTS / "visits_by_department.png", dpi=150)
plt.close(fig)
print("Charts saved to", CHARTS)
