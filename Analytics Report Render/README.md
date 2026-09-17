# Smart Report Analytics

A Render-ready Streamlit analytics application for attendance and operational reports. Users upload CSV/XLSX/XLS files and immediately receive management KPIs, interactive graphs, student attendance risk, staff workload, operational breakdowns, finance signals, data-quality diagnostics, filters and downloadable CSV outputs.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit and upload `sample_attendance_report.csv` to test.

## Deploy on Render

### Blueprint (recommended)
1. Extract this ZIP and push the files to a GitHub repository.
2. In Render choose **New > Blueprint**.
3. Connect the repository.
4. Render detects `render.yaml` and creates the web service.
5. Deploy. When the service is live, open its Render URL and upload a report.

### Manual Web Service
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
- Health check path: `/_stcore/health`

## Supported input
- CSV
- XLSX
- XLS

The app uses flexible column detection, so common variations such as Student Name/Learner Name, Staff Name/Teacher Name, Subject/Course, and Status/Attendance Status can work without changing code.

## Analytics included
- Executive KPIs: records, students, staff, attendance rate, absences and late records
- Attendance-status composition
- Monthly activity and monthly attendance trend
- Student-level table with Present, Absent, Late, Attendance %, and risk band
- Risk bands: High Risk <75%, Watch 75–<90%, Healthy >=90%
- Staff workload and associated student attendance rate
- Subject, batch and location breakdowns
- Invoice-status and numeric fee signals when available
- Data quality: missingness, uniqueness, exact duplicates, completeness and detected schema
- Interactive filters
- Student-risk and filtered-data CSV downloads

## Important interpretation notes
- Attendance risk is an operational rule, not a predictive ML model.
- Staff workload is volume and must not be interpreted as staff quality.
- Fee totals are shown only when numeric values can be parsed. Confirm the business grain before interpreting repeated attendance-row fees as revenue.
- Missing/unknown billing values are not treated as paid or overdue.

## Files
- `app.py` — Streamlit UI/dashboard
- `analytics_engine.py` — parsing, schema detection and analytics functions
- `requirements.txt` — pinned Python dependencies
- `render.yaml` — Render Blueprint configuration
- `.streamlit/config.toml` — Streamlit server settings
- `sample_attendance_report.csv` — test report supplied for this project

## Production improvements
For confidential institutional data, use a paid/private deployment and add authentication, database-backed upload history, retention controls, role-based access and encrypted persistent storage. The current version intentionally performs analysis in the active app session and does not implement user accounts or long-term report storage.
