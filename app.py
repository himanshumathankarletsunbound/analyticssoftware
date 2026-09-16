import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from analytics_engine import read_upload, prepare, attendance_rate, student_table, kpis

st.set_page_config(page_title='Smart Report Analytics', page_icon='📊', layout='wide')
st.markdown('''<style>.block-container{padding-top:1.2rem}.stMetric{border:1px solid rgba(128,128,128,.18);padding:12px;border-radius:14px}</style>''', unsafe_allow_html=True)
st.title('📊 Smart Report Analytics')
st.caption('Upload an attendance/operations CSV or Excel report and receive management-ready analytics automatically.')

with st.sidebar:
    st.header('Upload report')
    uploaded=st.file_uploader('CSV / XLSX / XLS',type=['csv','xlsx','xls'])
    st.caption('Analysis is performed in this app session. Files are not intentionally persisted by the application.')

if not uploaded:
    st.info('Upload a report from the sidebar to begin.')
    st.markdown('### Included analytics\nExecutive KPIs • attendance trends • student risk • staff workload • subject/batch/location breakdowns • finance signals • data-quality checks • downloadable CSV outputs')
    st.stop()

try:
    raw=read_upload(uploaded); df,s=prepare(raw)
except Exception as e:
    st.error(f'Unable to process this file: {e}'); st.stop()

with st.sidebar:
    st.divider(); st.header('Filters'); filtered=df.copy()
    if s['date'] and df['_date'].notna().any():
        lo,hi=df['_date'].min().date(),df['_date'].max().date(); dr=st.date_input('Date range',(lo,hi),lo,hi)
        if isinstance(dr,(tuple,list)) and len(dr)==2: filtered=filtered[(filtered['_date'].dt.date>=dr[0])&(filtered['_date'].dt.date<=dr[1])]
    for label,col in [('Student',s['student_name']),('Staff',s['staff']),('Subject',s['subject']),('Batch',s['batch']),('Location',s['location'])]:
        if col:
            vals=sorted(filtered[col].dropna().astype(str).unique().tolist()); sel=st.multiselect(label,vals)
            if sel: filtered=filtered[filtered[col].astype(str).isin(sel)]

K=kpis(filtered,s)
st.subheader('Executive overview')
cs=st.columns(6)
for c,(lab,val) in zip(cs,[('Records',f"{K['records']:,}"),('Students',f"{K['students']:,}" if K['students'] is not None else 'N/A'),('Staff',f"{K['staff']:,}" if K['staff'] is not None else 'N/A'),('Attendance',f"{K['attendance_rate']:.1f}%" if not np.isnan(K['attendance_rate']) else 'N/A'),('Absent',f"{K['absent']:,}"),('Late',f"{K['late']:,}")]): c.metric(lab,val)

tabs=st.tabs(['🏠 Executive','👨‍🎓 Students','👨‍🏫 Staff','📚 Operations','💰 Finance','🧹 Data Quality','🔎 Data'])
with tabs[0]:
    a,b=st.columns(2)
    with a:
        st.markdown('#### Attendance status')
        if s['status']:
            x=filtered[s['status']].fillna('Unknown').astype(str).value_counts().rename_axis('Status').reset_index(name='Records')
            st.plotly_chart(px.pie(x,names='Status',values='Records',hole=.5),use_container_width=True)
        else: st.info('No status column detected.')
    with b:
        st.markdown('#### Monthly activity')
        if s['date'] and filtered['_date'].notna().any():
            x=filtered.groupby('_month').size().reset_index(name='Records')
            st.plotly_chart(px.line(x,x='_month',y='Records',markers=True,labels={'_month':'Month'}),use_container_width=True)
        else: st.info('No usable date column detected.')
    if s['date'] and s['status'] and filtered['_date'].notna().any():
        x=filtered.groupby('_month')[s['status']].apply(attendance_rate).reset_index(name='Attendance %')
        fig=px.line(x,x='_month',y='Attendance %',markers=True,labels={'_month':'Month'}); fig.update_yaxes(range=[0,100]); st.plotly_chart(fig,use_container_width=True)
    st.markdown('#### Management observations')
    notes=[f"Current selection contains **{len(filtered):,} records**."]
    if s['status']: notes += [f"Attendance is **{K['attendance_rate']:.1f}%** across classifiable present/absent records.",f"There are **{K['absent']:,} absence records** in the current selection."]
    if s['invoice_status']:
        od=filtered[s['invoice_status']].astype(str).str.contains('overdue',case=False,na=False).sum()
        if od: notes.append(f"**{od:,} records** carry an overdue invoice flag.")
    for n in notes: st.write('• '+n)

with tabs[1]:
    t=student_table(filtered,s)
    if len(t):
        c1,c2,c3=st.columns(3); c1.metric('High risk (<75%)',int((t.Risk=='High Risk').sum())); c2.metric('Watch (75–<90%)',int((t.Risk=='Watch').sum())); c3.metric('Healthy (≥90%)',int((t.Risk=='Healthy').sum()))
        st.dataframe(t,use_container_width=True,hide_index=True,column_config={'Attendance %':st.column_config.ProgressColumn('Attendance %',min_value=0,max_value=100,format='%.1f%%')})
        st.download_button('Download student risk report',t.to_csv(index=False).encode(),file_name='student_risk_report.csv',mime='text/csv')
        key=s['student_name'] or s['student_id']; n=st.slider('Students in risk chart',5,30,15); p=t.dropna(subset=['Attendance %']).head(n).sort_values('Attendance %'); st.plotly_chart(px.bar(p,x='Attendance %',y=key,orientation='h',range_x=[0,100]),use_container_width=True)
    else: st.info('Student + attendance status fields are required.')

with tabs[2]:
    if s['staff']:
        t=filtered.groupby(s['staff']).size().reset_index(name='Records').sort_values('Records',ascending=False)
        if s['status']: t=t.merge(filtered.groupby(s['staff'])[s['status']].apply(attendance_rate).reset_index(name='Student Attendance %'),on=s['staff'],how='left')
        st.dataframe(t,use_container_width=True,hide_index=True); p=t.head(20).sort_values('Records'); st.plotly_chart(px.bar(p,x='Records',y=s['staff'],orientation='h'),use_container_width=True); st.caption('Workload volume is not a teacher-quality score.')
    else: st.info('No staff column detected.')

with tabs[3]:
    any_dim=False
    for label,col in [('Subject',s['subject']),('Batch',s['batch']),('Location',s['location'])]:
        if col:
            any_dim=True; st.markdown('#### '+label); t=filtered.groupby(col).size().reset_index(name='Records').sort_values('Records',ascending=False)
            if s['status']: t=t.merge(filtered.groupby(col)[s['status']].apply(attendance_rate).reset_index(name='Attendance %'),on=col,how='left')
            st.dataframe(t.head(50),use_container_width=True,hide_index=True); p=t.head(20).sort_values('Records'); st.plotly_chart(px.bar(p,x='Records',y=col,orientation='h'),use_container_width=True)
    if not any_dim: st.info('No subject, batch or location dimensions detected.')

with tabs[4]:
    if s['invoice_status']:
        x=filtered[s['invoice_status']].fillna('Unknown').astype(str).value_counts().rename_axis('Invoice Status').reset_index(name='Records'); a,b=st.columns(2); a.dataframe(x,use_container_width=True,hide_index=True); b.plotly_chart(px.pie(x,names='Invoice Status',values='Records',hole=.5),use_container_width=True)
    if s['fees'] and filtered['_fee_numeric'].notna().any():
        x=filtered['_fee_numeric'].dropna(); a,b,c=st.columns(3); a.metric('Numeric fee total',f'{x.sum():,.2f}'); b.metric('Average numeric fee',f'{x.mean():,.2f}'); c.metric('Numeric fee rows',f'{len(x):,}'); st.warning('Confirm whether fees are per session, per invoice, or repeated before treating totals as revenue.')
    elif not s['invoice_status']: st.info('No finance fields detected.')

with tabs[5]:
    rows,cols=raw.shape; dup=int(raw.duplicated().sum()); miss=int(raw.isna().sum().sum()); comp=100*(1-miss/(rows*cols)) if rows*cols else 0
    a,b,c,d=st.columns(4); a.metric('Rows',f'{rows:,}'); b.metric('Columns',cols); c.metric('Exact duplicates',f'{dup:,}'); d.metric('Cell completeness',f'{comp:.1f}%')
    q=pd.DataFrame({'Column':raw.columns,'Type':[str(raw[c].dtype) for c in raw.columns],'Missing':[int(raw[c].isna().sum()) for c in raw.columns],'Missing %':[100*raw[c].isna().mean() for c in raw.columns],'Unique':[int(raw[c].nunique(dropna=True)) for c in raw.columns]}).sort_values('Missing %',ascending=False)
    st.dataframe(q,use_container_width=True,hide_index=True,column_config={'Missing %':st.column_config.ProgressColumn('Missing %',min_value=0,max_value=100,format='%.1f%%')})
    st.markdown('#### Detected analytics schema'); st.dataframe(pd.DataFrame([(k,v) for k,v in s.items()],columns=['Field','Detected column']),use_container_width=True,hide_index=True)

with tabs[6]:
    clean=filtered.drop(columns=[c for c in filtered.columns if c.startswith('_')],errors='ignore'); st.dataframe(clean,use_container_width=True,hide_index=True); st.download_button('Download filtered data',clean.to_csv(index=False).encode(),file_name='filtered_report.csv',mime='text/csv')
