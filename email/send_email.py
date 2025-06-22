import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional
import resend
import requests
import base64

class EmailSender:
    """Handle sending emails with PDF attachments using various providers"""
    
    def __init__(self, provider: str = "resend"):
        self.provider = provider.lower()
        
        if self.provider == "resend":
            self.resend_api_key = os.getenv("RESEND_API_KEY")
            if self.resend_api_key:
                resend.api_key = self.resend_api_key
        elif self.provider == "sendgrid":
            self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    
    def send_report_email_resend(self, to_email: str, company_name: str, 
                                pdf_path: str, subject: str = None) -> bool:
        """Send email using Resend API"""
        
        if not self.resend_api_key:
            raise ValueError("RESEND_API_KEY not found in environment variables")
        
        if subject is None:
            week_date = datetime.now().strftime("%B %d, %Y")
            subject = f"Fleet Audit Report – Week of {week_date}"
        
        # Read PDF file
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Prepare email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Fleet Audit Report - {company_name}</h2>
                
                <p>Dear Fleet Manager,</p>
                
                <p>Please find attached your weekly fleet audit report for <strong>{company_name}</strong>.</p>
                
                <p>This automated report analyzes your fleet's GPS logs, fuel card data, and job schedules to identify potential issues including:</p>
                
                <ul>
                    <li>🚨 Potential fuel theft</li>
                    <li>👻 Ghost jobs (scheduled but not visited)</li>
                    <li>⏰ Excessive vehicle idling</li>
                    <li>🌙 After-hours vehicle usage</li>
                </ul>
                
                <p>If you have any questions about the findings in this report, please don't hesitate to contact your fleet administrator.</p>
                
                <hr style="border: 1px solid #eee; margin: 20px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    This report was generated automatically by FleetAudit.io<br>
                    Report generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}<br>
                    <em>Confidential - This report contains sensitive fleet operation data</em>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Fleet Audit Report - {company_name}
        
        Dear Fleet Manager,
        
        Please find attached your weekly fleet audit report for {company_name}.
        
        This automated report analyzes your fleet's GPS logs, fuel card data, and job schedules to identify potential issues.
        
        If you have any questions about the findings in this report, please contact your fleet administrator.
        
        ---
        This report was generated automatically by FleetAudit.io
        Report generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
        Confidential - This report contains sensitive fleet operation data
        """
        
        try:
            # Send email with attachment
            params = {
                "from": "FleetAudit.io <reports@fleetaudit.io>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "attachments": [
                    {
                        "filename": f"fleet_audit_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        "content": base64.b64encode(pdf_content).decode(),
                    }
                ],
            }
            
            email_result = resend.Emails.send(params)
            return True
            
        except Exception as e:
            print(f"Failed to send email via Resend: {str(e)}")
            return False
    
    def send_report_email_sendgrid(self, to_email: str, company_name: str, 
                                  pdf_path: str, subject: str = None) -> bool:
        """Send email using SendGrid API"""
        
        if not self.sendgrid_api_key:
            raise ValueError("SENDGRID_API_KEY not found in environment variables")
        
        if subject is None:
            week_date = datetime.now().strftime("%B %d, %Y")
            subject = f"Fleet Audit Report – Week of {week_date}"
        
        # Read PDF file
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = base64.b64encode(pdf_file.read()).decode()
        
        # Prepare SendGrid payload
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": "reports@fleetaudit.io", "name": "FleetAudit.io"},
            "content": [
                {
                    "type": "text/plain",
                    "value": f"Fleet audit report for {company_name} is attached."
                },
                {
                    "type": "text/html",
                    "value": f"""
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2>Fleet Audit Report - {company_name}</h2>
                        <p>Your weekly fleet audit report is attached.</p>
                        <p>Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
                    </body>
                    </html>
                    """
                }
            ],
            "attachments": [
                {
                    "content": pdf_content,
                    "type": "application/pdf",
                    "filename": f"fleet_audit_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    "disposition": "attachment"
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 202:
                return True
            else:
                print(f"SendGrid API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Failed to send email via SendGrid: {str(e)}")
            return False
    
    def send_report_email_smtp(self, to_email: str, company_name: str, 
                              pdf_path: str, subject: str = None,
                              smtp_server: str = "smtp.gmail.com", 
                              smtp_port: int = 587,
                              smtp_user: str = None, smtp_password: str = None) -> bool:
        """Send email using SMTP (fallback option)"""
        
        if smtp_user is None:
            smtp_user = os.getenv("SMTP_USER")
        if smtp_password is None:
            smtp_password = os.getenv("SMTP_PASSWORD")
            
        if not smtp_user or not smtp_password:
            raise ValueError("SMTP credentials not provided")
        
        if subject is None:
            week_date = datetime.now().strftime("%B %d, %Y")
            subject = f"Fleet Audit Report – Week of {week_date}"
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Email body
            body = f"""
            Dear Fleet Manager,
            
            Please find attached your weekly fleet audit report for {company_name}.
            
            This automated report analyzes your fleet data to identify potential issues.
            
            Best regards,
            FleetAudit.io System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= fleet_audit_report_{datetime.now().strftime("%Y%m%d")}.pdf'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email via SMTP: {str(e)}")
            return False
    
    def send_report_email(self, to_email: str, company_name: str, 
                         pdf_path: str, subject: str = None) -> bool:
        """Send email using the configured provider"""
        
        if self.provider == "resend":
            return self.send_report_email_resend(to_email, company_name, pdf_path, subject)
        elif self.provider == "sendgrid":
            return self.send_report_email_sendgrid(to_email, company_name, pdf_path, subject)
        elif self.provider == "smtp":
            return self.send_report_email_smtp(to_email, company_name, pdf_path, subject)
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration"""
        
        test_subject = "FleetAudit.io Test Email"
        test_content = """
        <html>
        <body>
            <h2>FleetAudit.io Test Email</h2>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p>If you received this email, your FleetAudit.io system is ready to send reports!</p>
        </body>
        </html>
        """
        
        if self.provider == "resend":
            try:
                params = {
                    "from": "FleetAudit.io <reports@fleetaudit.io>",
                    "to": [to_email],
                    "subject": test_subject,
                    "html": test_content,
                }
                
                resend.Emails.send(params)
                return True
            except Exception as e:
                print(f"Test email failed: {str(e)}")
                return False
        
        # Add other provider test methods as needed
        return False

# Convenience function for easy email sending
def send_audit_report(to_email: str, pdf_path: str, company_name: str, 
                     provider: str = "resend") -> bool:
    """Convenience function to send audit report email"""
    
    sender = EmailSender(provider)
    return sender.send_report_email(to_email, company_name, pdf_path)