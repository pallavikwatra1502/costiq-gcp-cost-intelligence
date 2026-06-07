# CostIQ — GCP Cloud Cost Intelligence Platform

CostIQ is a GCP FinOps and data engineering project that analyses cloud billing, BigQuery utilisation, Dataflow jobs and storage metadata to detect cost waste, forecast budget risk, generate owner alerts and provide official guidance-backed optimisation recommendations.

## Live Demo

Add your Streamlit URL here after deployment.

## Key Features

- Executive cloud cost dashboard
- Service and project-level cost explorer
- BigQuery query cost optimiser
- BigQuery table storage explorer
- Dataflow job cost and runtime optimiser
- Budget guardrails and forecasted overspend detection
- Real email alert workflow using Gmail App Password
- Recommendation engine with official Google Cloud documentation links
- Ask CostIQ assistant for cost troubleshooting
- Cost anomaly detection
- Sample GCP-style billing and engineering datasets

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app/main.py 
```

## Streamlit Cloud Deployment

Main file path:

```text
app/main.py
```

## Email Security Note

The real email alert feature uses Gmail SMTP and an App Password. Do not hardcode credentials in code or commit them to GitHub.
