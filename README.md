# Smart Report Analytics

A Heroku- and Render-ready Streamlit analytics application for attendance and operational reports. Users upload CSV/XLSX/XLS files and immediately receive management KPIs, interactive graphs, student attendance risk, staff workload, operational breakdowns, finance signals, data-quality diagnostics, filters and downloadable CSV outputs.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit and upload `sample_attendance_report.csv` to test.

## Deploy on Heroku

This repository includes the required `Procfile`, `.python-version`, and `app.json` files. No database or Heroku add-ons are required for the current session-based application.

### Heroku Dashboard with GitHub

1. Push the repository to GitHub.
2. In the Heroku Dashboard, select **New > Create new app**.
3. On the app's **Deploy** tab, choose **GitHub** and connect this repository.
4. Select the `main` branch and click **Deploy Branch**.
5. Optionally enable automatic deploys after the first successful deployment.

### Heroku CLI

Install the Heroku CLI and log in, then run:

```bash
heroku create YOUR_UNIQUE_APP_NAME --stack heroku-24
git push heroku main
heroku open
```

For an existing Heroku app, attach it first:

```bash
heroku git:remote -a YOUR_EXISTING_APP_NAME
git push heroku main
```

Useful diagnostics:

```bash
heroku ps
heroku logs --tail
```

Heroku supplies the required `PORT` environment variable automatically. The `Procfile` binds Streamlit to that port and to `0.0.0.0` so the Heroku router can reach it.

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
- `Procfile` — Heroku web-process command
- `.python-version` — Python runtime selected for Heroku
- `app.json` — Heroku app metadata and buildpack declaration
- `render.yaml` — Render Blueprint configuration
- `.streamlit/config.toml` — Streamlit server settings
- `sample_attendance_report.csv` — test report supplied for this project

## Production improvements
For confidential institutional data, use a paid/private deployment and add authentication, database-backed upload history, retention controls, role-based access and encrypted persistent storage. The current version intentionally performs analysis in the active app session and does not implement user accounts or long-term report storage.
