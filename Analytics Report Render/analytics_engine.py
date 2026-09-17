import io, re
import numpy as np
import pandas as pd


def norm_col(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).strip().lower()).strip()


def find_col(df, candidates):
    normalized = {norm_col(c): c for c in df.columns}
    for x in candidates:
        if norm_col(x) in normalized:
            return normalized[norm_col(x)]
    for c in df.columns:
        nc = norm_col(c)
        for x in candidates:
            nx = norm_col(x)
            if nx and (nx in nc or nc in nx):
                return c
    return None


def read_upload(file):
    name = getattr(file, 'name', '').lower()
    raw = file.getvalue() if hasattr(file, 'getvalue') else file.read()
    if name.endswith('.csv'):
        for enc in ['utf-8-sig', 'utf-8', 'latin1']:
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=enc)
            except Exception:
                pass
        raise ValueError('Could not read CSV encoding.')
    if name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(raw))
    raise ValueError('Upload CSV, XLSX or XLS.')


def parse_money(series):
    cleaned = (series.astype(str).str.replace(',', '', regex=False)
               .str.replace(r'[₹$£€]', '', regex=True)
               .str.extract(r'([-+]?\d*\.?\d+)', expand=False))
    return pd.to_numeric(cleaned, errors='coerce')


def status_bucket(x):
    s = str(x).strip().lower()
    if not s or s == 'nan': return 'Unknown'
    if 'absent' in s: return 'Absent'
    if 'late' in s: return 'Late'
    if 'left early' in s or 'early' in s: return 'Left Early'
    if 'present' in s or 'checked' in s or 'check-in' in s or 'check in' in s: return 'Present'
    return str(x).strip().title()


def detect_schema(df):
    return {
        'student_id': find_col(df, ['Student ID','Student Id','Learner ID']),
        'student_name': find_col(df, ['Student Name','Learner Name']),
        'subject': find_col(df, ['Subject','Course','Class','Program']),
        'staff': find_col(df, ['Staff Name','Teacher Name','Tutor','Instructor','Staff']),
        'location': find_col(df, ['Location','Mode','Venue']),
        'batch': find_col(df, ['Batch Name','Batch','Group']),
        'status': find_col(df, ['Status','Attendance Status','Attendance']),
        'date': find_col(df, ['Date','Class Date','Session Date','Attendance Date']),
        'start_time': find_col(df, ['Start Time']),
        'end_time': find_col(df, ['End Time']),
        'fees': find_col(df, ['Fees','Fee','Amount','Price']),
        'invoice_no': find_col(df, ['Invoice Number','Invoice No']),
        'invoice_status': find_col(df, ['Invoice Status','Payment Status']),
        'item_name': find_col(df, ['Item Name','Item','Service']),
        'marked_by': find_col(df, ['Marked By','Created By']),
        'marked_at': find_col(df, ['Marked At','Created At','Updated At']),
    }


def prepare(df):
    df = df.copy(); df.columns = [str(c).strip() for c in df.columns]
    s = detect_schema(df)
    if s['date']:
        df['_date'] = pd.to_datetime(df[s['date']], errors='coerce')
        df['_month'] = df['_date'].dt.to_period('M').astype(str)
        df['_weekday'] = df['_date'].dt.day_name()
    else:
        df['_date'] = pd.NaT; df['_month'] = 'Unknown'; df['_weekday'] = 'Unknown'
    df['_status_bucket'] = df[s['status']].map(status_bucket) if s['status'] else 'Unknown'
    df['_fee_numeric'] = parse_money(df[s['fees']]) if s['fees'] else np.nan
    return df, s


def attendance_rate(series):
    b = series.map(status_bucket)
    p = b.isin(['Present','Late','Left Early']).sum(); a = (b == 'Absent').sum()
    return 100*p/(p+a) if p+a else np.nan


def student_table(df, schema):
    key = schema['student_name'] or schema['student_id']
    if not key or not schema['status']: return pd.DataFrame()
    g = df.groupby(key, dropna=False)
    out = g.size().rename('Total Records').to_frame()
    out['Present'] = g['_status_bucket'].apply(lambda x: x.isin(['Present','Late','Left Early']).sum())
    out['Absent'] = g['_status_bucket'].apply(lambda x: (x=='Absent').sum())
    out['Late'] = g['_status_bucket'].apply(lambda x: (x=='Late').sum())
    denom = out['Present'] + out['Absent']
    out['Attendance %'] = np.where(denom > 0, 100*out['Present']/denom, np.nan)
    out['Risk'] = pd.cut(out['Attendance %'], [-np.inf,75,90,np.inf], right=False, labels=['High Risk','Watch','Healthy'])
    return out.reset_index().sort_values(['Attendance %','Absent'], ascending=[True,False])


def kpis(df, schema):
    b=df['_status_bucket']; p=b.isin(['Present','Late','Left Early']).sum(); a=(b=='Absent').sum()
    key=schema['student_id'] or schema['student_name']
    return {'records':len(df),'students':df[key].nunique(dropna=True) if key else None,
            'staff':df[schema['staff']].nunique(dropna=True) if schema['staff'] else None,
            'present':int(p),'absent':int(a),'late':int((b=='Late').sum()),
            'attendance_rate':100*p/(p+a) if p+a else np.nan}
