import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from core.cost_engine import forecast_month_end, savings_opportunities, executive_kpis
from core.email_engine import build_budget_alert_email, send_email_gmail
from core.assistant import answer
st.set_page_config(page_title='CostIQ GCP', page_icon='💸', layout='wide')
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
st.markdown("""<style>.block-container{padding-top:1rem;max-width:1320px}[data-testid='stAppViewContainer']{background:radial-gradient(circle at top right,rgba(102,227,255,.16),transparent 30%),#071018;color:#eef6ff}[data-testid='stSidebar']{background:#0d1622}.hero{padding:34px;border-radius:30px;border:1px solid rgba(102,227,255,.22);background:linear-gradient(135deg,rgba(17,27,39,.96),rgba(7,16,24,.96));margin-bottom:22px}.eyebrow{color:#66e3ff;letter-spacing:5px;text-transform:uppercase;font-weight:800;font-size:13px}.hero h1{font-size:56px;line-height:1.02;margin:.3rem 0;color:#eef6ff}.hero p{font-size:18px;color:#aab8c8;max-width:980px}.small{color:#aab8c8}.stTabs [data-baseweb='tab']{border-radius:999px;background:rgba(255,255,255,.06);padding:10px 18px}</style>""", unsafe_allow_html=True)
@st.cache_data
def load_all():
    return (pd.read_csv(DATA/'gcp_billing_export_sample.csv'),pd.read_csv(DATA/'bigquery_jobs_sample.csv'),pd.read_csv(DATA/'bigquery_tables_sample.csv'),pd.read_csv(DATA/'dataflow_jobs_sample.csv'),pd.read_csv(DATA/'gcp_optimization_knowledge_base.csv'))
billing,bq_jobs,bq_tables,dataflow,kb=load_all()
st.sidebar.title('CostIQ'); st.sidebar.caption('GCP cost intelligence, FinOps guardrails and optimisation guidance.')
up=st.sidebar.file_uploader('Upload billing CSV', type=['csv'])
if up: billing=pd.read_csv(up)
proj=st.sidebar.multiselect('Project', sorted(billing.project_id.unique())); svc=st.sidebar.multiselect('Service', sorted(billing.service.unique()))
if proj:
    billing=billing[billing.project_id.isin(proj)]; bq_jobs=bq_jobs[bq_jobs.project_id.isin(proj)]; bq_tables=bq_tables[bq_tables.project_id.isin(proj)]; dataflow=dataflow[dataflow.project_id.isin(proj)]
if svc: billing=billing[billing.service.isin(svc)]
st.markdown("""<div class='hero'><div class='eyebrow'>GCP FinOps • BigQuery • Dataflow • Budget Automation</div><h1>CostIQ — GCP Cloud Cost Intelligence</h1><p>Analyses GCP billing, BigQuery utilisation, Dataflow jobs and storage patterns to detect waste, forecast budget risk, generate owner alerts and provide official guidance-backed optimisation recommendations.</p><p class='small'>Created by Pallavi Kwatra</p></div>""", unsafe_allow_html=True)
K=executive_kpis(billing,bq_jobs,bq_tables,dataflow); cols=st.columns(6)
for c,label,key in zip(cols,['Current Spend','Forecast Spend','Budget','Potential Savings','Anomalies','Projects at Risk'],['current_spend','forecast_spend','budget_total','potential_savings','anomaly_count','projects_at_risk']):
    val=K[key]; c.metric(label, f"GBP {val:,.0f}" if isinstance(val,float) else val)
tabs=st.tabs(['Overview','Cost Explorer','BigQuery Optimiser','Dataflow Optimiser','Budget Guardrails','Recommendations','Ask CostIQ','Architecture'])
with tabs[0]:
    st.subheader('Executive Overview'); c1,c2=st.columns(2)
    with c1:
        x=billing.groupby('service',as_index=False).cost_gbp.sum().sort_values('cost_gbp',ascending=False); fig=px.bar(x,x='service',y='cost_gbp',title='Cost by GCP Service'); fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
    with c2:
        x=billing.groupby('project_id',as_index=False).cost_gbp.sum().sort_values('cost_gbp',ascending=False); fig=px.pie(x,names='project_id',values='cost_gbp',title='Spend by Project'); fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
    st.dataframe(savings_opportunities(billing,bq_jobs,bq_tables,dataflow),use_container_width=True)
with tabs[1]:
    daily=billing.groupby(['usage_date','service'],as_index=False).cost_gbp.sum(); fig=px.line(daily,x='usage_date',y='cost_gbp',color='service',title='Daily Service Cost Trend'); fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True); st.dataframe(billing.sort_values('cost_gbp',ascending=False),use_container_width=True)
with tabs[2]:
    st.subheader('BigQuery Optimiser'); c1,c2,c3,c4=st.columns(4); c1.metric('Jobs Analysed',len(bq_jobs)); c2.metric('Total TB Processed',f"{bq_jobs.bytes_processed_tb.sum():,.1f}"); c3.metric('Estimated Query Cost',f"GBP {bq_jobs.estimated_cost_gbp.sum():,.0f}"); c4.metric('No Partition Filter',int((bq_jobs.partition_filter_used=='No').sum()))
    high=bq_jobs.sort_values('estimated_cost_gbp',ascending=False).head(15); fig=px.bar(high,x='job_id',y='estimated_cost_gbp',color='partition_filter_used',title='Most Expensive BigQuery Jobs'); fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True); st.dataframe(bq_tables.sort_values('storage_cost_gbp_month',ascending=False),use_container_width=True)
with tabs[3]:
    st.subheader('Dataflow Optimiser'); fig=px.scatter(dataflow,x='runtime_hours',y='estimated_cost_gbp',size='worker_count',color='avg_cpu_utilisation_pct',hover_name='job_name',title='Dataflow Runtime vs Cost'); fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True); st.dataframe(dataflow.sort_values('estimated_cost_gbp',ascending=False),use_container_width=True)
with tabs[4]:
    st.subheader('Budget Guardrails & Real Email Alerting'); fc=forecast_month_end(billing); st.dataframe(fc,use_container_width=True); selected=st.selectbox('Select project for alert',fc.project_id.tolist()); row=fc[fc.project_id==selected].iloc[0]
    drivers=billing[billing.project_id==selected].groupby('service').cost_gbp.sum().sort_values(ascending=False).head(3); driver_text='\n'.join([f'- {s}: GBP {c:,.2f}' for s,c in drivers.items()]); subject,body=build_budget_alert_email(row.project_id,row.owner_email,row.monthly_budget_gbp,row.cost_gbp,row.forecast_month_end_gbp,row.expected_overspend_gbp,driver_text)
    st.text_input('Recipient',value=row.owner_email); st.text_input('Subject',value=subject); st.text_area('Email body',value=body,height=330); st.download_button('Download Alert Email',body,file_name=f'{selected}_cost_alert.txt')
    with st.expander('Send real email using Gmail App Password'):
        st.warning('Use only your own Gmail App Password. Never commit secrets to GitHub.'); sender=st.text_input('Sender Gmail'); pwd=st.text_input('Gmail App Password',type='password'); recip=st.text_input('Recipient email',value=row.owner_email)
        if st.button('Send Email Alert'):
            try: send_email_gmail(sender,pwd,recip,subject,body); st.success('Email alert sent successfully.')
            except Exception as e: st.error(f'Email failed: {e}')
with tabs[5]:
    st.subheader('Recommendation Center with Official GCP Guidance'); st.dataframe(savings_opportunities(billing,bq_jobs,bq_tables,dataflow),use_container_width=True)
    for _,r in kb.iterrows(): st.markdown(f"**{r.issue}**"); st.write(r.recommendation); st.caption(r.official_doc_url)
with tabs[6]:
    examples=['Why is BigQuery cost high?','Which Dataflow job is expensive?','Which project will exceed budget?','How can I reduce storage cost?','Show cost anomalies','What should I optimise first?']; selected=st.selectbox('Example questions',['']+examples); q=st.text_input('Ask your cost question',value=selected)
    if st.button('Ask CostIQ'): st.markdown(answer(q,billing,bq_jobs,bq_tables,dataflow,kb))
with tabs[7]:
    st.code('''GCP Billing Export / BigQuery Jobs / Storage Metadata / Dataflow Jobs
  ↓
CostIQ Data Ingestion Layer
  ↓
Cost Normalisation + Forecasting
  ↓
Optimisation Engines: BigQuery, Dataflow, Storage, Budgets, Anomalies
  ↓
Recommendation Engine: Root Cause + Estimated Saving + Official GCP Guidance
  ↓
Automation Layer: Owner Mapping + Budget Breach Detection + Real Email Alert
  ↓
Executive Dashboard + Ask CostIQ Assistant''',language='text')
