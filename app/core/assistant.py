from .cost_engine import forecast_month_end, detect_cost_anomalies, savings_opportunities
from .recommendation_engine import match_guidance

def answer(question,billing,bq_jobs,bq_tables,dataflow,kb):
    q=(question or '').lower().strip()
    if 'bigquery' in q or 'bq' in q or 'query' in q:
        high=bq_jobs.sort_values('estimated_cost_gbp',ascending=False).head(5); g=match_guidance(kb,'BigQuery high query cost')
        return 'BigQuery cost diagnosis:\n'+'\n'.join([f'- {r.job_id}: {r.bytes_processed_tb} TB scanned, GBP {r.estimated_cost_gbp}, partition filter: {r.partition_filter_used}' for r in high.itertuples()])+'\n\nOfficial GCP guidance:\n'+'\n'.join([f'- {r.issue}: {r.recommendation} ({r.official_doc_url})' for r in g.itertuples()])
    if 'dataflow' in q or 'job' in q or 'worker' in q:
        high=dataflow.sort_values('estimated_cost_gbp',ascending=False).head(5); g=match_guidance(kb,'Dataflow expensive job')
        return 'Dataflow cost diagnosis:\n'+'\n'.join([f'- {r.job_name}: {r.runtime_hours} hours, {r.worker_count} workers, GBP {r.estimated_cost_gbp}' for r in high.itertuples()])+'\n\nOfficial GCP guidance:\n'+'\n'.join([f'- {r.issue}: {r.recommendation} ({r.official_doc_url})' for r in g.itertuples()])
    if 'budget' in q or 'overspend' in q or 'alert' in q:
        fc=forecast_month_end(billing).head(5); return 'Budget guardrail summary:\n'+'\n'.join([f'- {r.project_id}: {r.budget_status}, forecast GBP {r.forecast_month_end_gbp}, budget GBP {r.monthly_budget_gbp}, usage {r.budget_usage_pct}%' for r in fc.itertuples()])
    if 'anomaly' in q or 'spike' in q:
        an=detect_cost_anomalies(billing).head(8)
        return 'No major cost anomalies detected.' if an.empty else 'Detected cost anomalies:\n'+'\n'.join([f'- {r.usage_date.date()} | {r.project_id} | {r.service}: GBP {r.cost_gbp}, {r.anomaly_score}x baseline' for r in an.itertuples()])
    if 'storage' in q or 'table' in q:
        stale=bq_tables.sort_values(['last_accessed_days','storage_cost_gbp_month'],ascending=False).head(8); g=match_guidance(kb,'BigQuery storage growth')
        return 'Storage optimisation candidates:\n'+'\n'.join([f'- {r.dataset}.{r.table_name}: {r.size_gb} GB, last accessed {r.last_accessed_days} days, expiry {r.expiration_policy}' for r in stale.itertuples()])+'\n\nGuidance:\n'+'\n'.join([f'- {r.recommendation} ({r.official_doc_url})' for r in g.itertuples()])
    if 'save' in q or 'optimise' in q or 'optimize' in q or 'recommend' in q:
        opp=savings_opportunities(billing,bq_jobs,bq_tables,dataflow); return 'Top optimisation opportunities:\n'+'\n'.join([f'- {r.opportunity}: estimated saving GBP {r.estimated_saving_gbp} | {r.recommended_action}' for r in opp.itertuples()])
    g=match_guidance(kb,q)
    return 'CostIQ guidance:\n'+'\n'.join([f'- {r.issue}: {r.recommendation}\n  Official doc: {r.official_doc_url}' for r in g.itertuples()])
