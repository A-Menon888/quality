# Human Escalation Setup Guide

## Overview
The Quality Assurance Assistant now includes automatic human escalation when the chatbot is not confident in its responses. This feature sends an email to designated personnel when the confidence level drops below 30%.

## Configuration Steps

### 1. Email Account Setup
You'll need an email account for sending escalation emails. Gmail is recommended.

**For Gmail:**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an "App Password" for the application
3. Use this app password (not your regular password) in the configuration

### 2. Streamlit Secrets Configuration
Add these secrets to your Streamlit configuration:

**Option A: Using .streamlit/secrets.toml file:**
```toml
[secrets]
ESCALATION_EMAIL = "your-email@gmail.com"
ESCALATION_PASSWORD = "your-16-character-app-password"
MANAGER_EMAIL = "manager@company.com"
```

**Option B: Using Streamlit Cloud secrets:**
In your Streamlit Cloud dashboard, add these secrets:
- `ESCALATION_EMAIL`: Your email address
- `ESCALATION_PASSWORD`: Your app password
- `MANAGER_EMAIL`: Manager's email address

### 3. Test the Configuration
1. Run your Streamlit app
2. In the sidebar, click "🔧 Test Email Connection"
3. You should see "✅ Email connection successful!" if configured correctly

## How It Works

### Escalation Triggers
The system escalates when:
- **Confidence Score < 30%**
- Response contains uncertainty phrases like "I don't know", "I'm not sure"
- Tool generation requests fail
- Responses are too generic or unhelpful
- Error messages are present

### What Happens During Escalation
1. **Email Sent**: Automatic email to the manager with:
   - Original user query
   - Bot's response
   - Confidence score
   - Timestamp

2. **User Notification**: User sees a warning message:
   ```
   ⚠️ Low Confidence Response
   
   I'm not entirely confident in my answer above. I've escalated your query to our human quality experts who will review it and get back to you.
   
   Confidence Level: 25%
   Escalation Status: ✅ Sent
   ```

### Confidence Scoring
The system assesses confidence based on:
- **Uncertainty phrases**: -0.2 points each
- **Short responses to complex queries**: -0.3 points
- **Failed tool recommendations**: -0.2 points
- **Generic responses**: -0.1 points
- **Error messages**: -0.3 points

## Customization

### Adjust Escalation Threshold
In `qa_bot.py`, line 545:
```python
ESCALATION_THRESHOLD = 0.3  # Change to 0.2 for more sensitive, 0.4 for less sensitive
```

### Add More Uncertainty Phrases
In `qa_bot.py`, lines 483-487:
```python
uncertainty_phrases = [
    "i don't know", "i'm not sure", "i can't", "unable to",
    "not certain", "might be", "could be", "possibly",
    "i don't have", "not available", "unclear", "ambiguous",
    "your custom phrase here"  # Add your own phrases
]
```

### Change Email Template
In `email_config.py`, modify the `send_escalation_email` method to customize the email content.

## Troubleshooting

### Email Not Sending
1. Check your app password is correct
2. Ensure 2FA is enabled on your email account
3. Verify the email addresses are correct
4. Check your internet connection

### False Escalations
1. Increase the `ESCALATION_THRESHOLD` value
2. Remove overly sensitive phrases from `uncertainty_phrases`
3. Adjust the confidence scoring logic

### No Escalations When Expected
1. Decrease the `ESCALATION_THRESHOLD` value
2. Add more uncertainty phrases
3. Check the confidence scoring logic

## Security Notes
- Never commit email passwords to version control
- Use app passwords, not regular passwords
- Consider using environment variables for production
- Regularly rotate app passwords

## Support
If you encounter issues with the escalation system, check:
1. Email configuration is correct
2. Network connectivity
3. Streamlit secrets are properly set
4. All required dependencies are installed
