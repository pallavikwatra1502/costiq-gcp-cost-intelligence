import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def build_budget_alert_email(project_id,owner_email,budget,current_spend,forecast,overspend,drivers):
    subject=f'CostIQ Alert: {project_id} forecasted to exceed monthly budget'
    body=f'''Hi Application Owner,

CostIQ has detected that your GCP project is forecasted to exceed the monthly budget.

Project: {project_id}
Monthly Budget: GBP {budget:,.2f}
Current Spend: GBP {current_spend:,.2f}
Forecast Month-End Spend: GBP {forecast:,.2f}
Expected Overspend: GBP {overspend:,.2f}

Primary Cost Drivers:
{drivers}

Recommended Actions:
1. Review BigQuery queries with high bytes processed.
2. Apply partition filters and table expiration where appropriate.
3. Review long-running Dataflow jobs and worker utilisation.
4. Investigate service-level cost anomalies.
5. Confirm whether the forecasted overspend is approved or requires remediation.

Regards,
CostIQ FinOps Automation
'''
    return subject,body

def send_email_gmail(sender_email,app_password,recipient_email,subject,body):
    msg=MIMEMultipart(); msg['From']=sender_email; msg['To']=recipient_email; msg['Subject']=subject; msg.attach(MIMEText(body,'plain'))
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
        server.login(sender_email,app_password); server.sendmail(sender_email,recipient_email,msg.as_string())
    return True
