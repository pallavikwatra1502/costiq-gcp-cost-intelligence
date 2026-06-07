import pandas as pd
import numpy as np

def forecast_month_end(billing):
    df=billing.copy(); df['usage_date']=pd.to_datetime(df['usage_date'])
    max_day=max(df['usage_date'].dt.day.max(),1); month_days=df['usage_date'].dt.days_in_month.max()
    cur=df.groupby(['project_id','owner_team','owner_email','monthly_budget_gbp'],as_index=False)['cost_gbp'].sum()
    cur['forecast_month_end_gbp']=(cur['cost_gbp']/max_day*month_days).round(2)
    cur['budget_usage_pct']=(cur['forecast_month_end_gbp']/cur['monthly_budget_gbp']*100).round(1)
    cur['expected_overspend_gbp']=(cur['forecast_month_end_gbp']-cur['monthly_budget_gbp']).clip(lower=0).round(2)
    cur['budget_status']=np.select([cur['budget_usage_pct']>=120,cur['budget_usage_pct']>=100,cur['budget_usage_pct']>=80],['Critical','Breaching','At Risk'],default='Healthy')
    return cur.sort_values('budget_usage_pct',ascending=False)

def detect_cost_anomalies(billing):
    df=billing.copy(); df['usage_date']=pd.to_datetime(df['usage_date'])
    daily=df.groupby(['usage_date','project_id','service'],as_index=False)['cost_gbp'].sum()
    daily['baseline']=daily.groupby(['project_id','service'])['cost_gbp'].transform('median')
    daily['anomaly_score']=(daily['cost_gbp']/daily['baseline'].replace(0,np.nan)).round(2)
    return daily[daily['anomaly_score']>=2.0].sort_values('anomaly_score',ascending=False)

def savings_opportunities(billing,bq_jobs,bq_tables,dataflow):
    opp=[]
    exp=bq_jobs[(bq_jobs['bytes_processed_tb']>10)&(bq_jobs['partition_filter_used']=='No')]
    if len(exp): opp.append(['BigQuery query optimisation',len(exp),round(exp['estimated_cost_gbp'].sum()*.25,2),'High','Apply partition filters, clustering and reduce scanned bytes.'])
    stale=bq_tables[(bq_tables['last_accessed_days']>180)&(bq_tables['expiration_policy']=='No')]
    if len(stale): opp.append(['BigQuery storage lifecycle',len(stale),round(stale['storage_cost_gbp_month'].sum()*.6,2),'Medium','Apply table expiration or archive stale tables.'])
    ineff=dataflow[(dataflow['runtime_hours']>24)&(dataflow['avg_cpu_utilisation_pct']<35)]
    if len(ineff): opp.append(['Dataflow worker right-sizing',len(ineff),round(ineff['estimated_cost_gbp'].sum()*.2,2),'High','Review autoscaling and reduce over-provisioned workers.'])
    an=detect_cost_anomalies(billing)
    if len(an): opp.append(['Cost anomaly investigation',len(an),round(an['cost_gbp'].sum()*.15,2),'High','Investigate service-level spikes and enforce budget guardrails.'])
    return pd.DataFrame(opp,columns=['opportunity','affected_items','estimated_saving_gbp','priority','recommended_action'])

def executive_kpis(billing,bq_jobs,bq_tables,dataflow):
    fc=forecast_month_end(billing); sav=savings_opportunities(billing,bq_jobs,bq_tables,dataflow); an=detect_cost_anomalies(billing)
    return {'current_spend':round(billing.cost_gbp.sum(),2),'forecast_spend':round(fc.forecast_month_end_gbp.sum(),2),'budget_total':round(fc.monthly_budget_gbp.sum(),2),'potential_savings':round(sav.estimated_saving_gbp.sum(),2) if not sav.empty else 0,'anomaly_count':len(an),'projects_at_risk':int(fc[fc.budget_status.isin(['At Risk','Breaching','Critical'])].shape[0])}
