import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import streamlit as st

class EmailEscalation:
    def __init__(self):
        # Email settings - using Streamlit secrets for configuration
        self.smtp_server = "smtp.gmail.com"  # or your email provider
        self.smtp_port = 587
        self.sender_email = st.secrets.get("ESCALATION_EMAIL", "aayushmenon27@gmail.com")
        self.sender_password = st.secrets.get("ESCALATION_PASSWORD", "afex usio kswl mzoy")
        self.recipient_email = st.secrets.get("MANAGER_EMAIL", "aayush.pmenon2023@vitstudent.ac.in")
    
    def send_escalation_email(self, user_query, chatbot_response, confidence_reason, recipient_email=None):
        """Send escalation email to human support"""
        try:
            # Use provided recipient email or fall back to default
            email_to = recipient_email or self.recipient_email
            
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email_to
            msg['Subject'] = f"QA Bot Escalation - LLM Determined Uncertainty"
            
            body = f"""
    The QA Assistant has determined that it needs human expertise to properly address this query.

    Escalation Reason: {confidence_reason}

    User Query: {user_query}

    Bot Response: {chatbot_response}

    Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    Please review and provide assistance.

    ---
    This is an automated escalation from the Quality Assurance Assistant.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, email_to, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Failed to send escalation email: {e}")
            return False
            
    def test_email_connection(self):
        """Test if email configuration is working"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            return True
        except Exception as e:
            print(f"Email connection test failed: {e}")
            return False
