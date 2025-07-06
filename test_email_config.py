#!/usr/bin/env python3
"""
Test script to verify email configuration works
Run this after setting up your email credentials
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys

def load_env_file(file_path):
    """Load environment variables from .env file"""
    config = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

def test_email_config():
    """Test the email configuration"""
    print("🔧 Testing Email Configuration...")
    print("=" * 50)
    
    # Load configuration
    config = load_env_file('email_reminders.env')
    
    # Check required fields
    required_fields = ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD']
    missing_fields = [field for field in required_fields if field not in config or not config[field]]
    
    if missing_fields:
        print(f"❌ Missing required configuration: {', '.join(missing_fields)}")
        print("Please update email_reminders.env with your credentials")
        return False
    
    # Display configuration (hide password)
    print(f"📧 SMTP Server: {config['SMTP_SERVER']}")
    print(f"🔌 SMTP Port: {config['SMTP_PORT']}")
    print(f"👤 Username: {config['SMTP_USERNAME']}")
    print(f"🔑 Password: {'*' * len(config['SMTP_PASSWORD'])}")
    print()
    
    # Test connection
    try:
        print("🔗 Testing SMTP connection...")
        server = smtplib.SMTP(config['SMTP_SERVER'], int(config['SMTP_PORT']))
        server.starttls()
        
        print("🔐 Authenticating...")
        server.login(config['SMTP_USERNAME'], config['SMTP_PASSWORD'])
        print("✅ Authentication successful!")
        
        # Send test email
        print("📤 Sending test email...")
        
        msg = MIMEMultipart()
        msg['From'] = config['SMTP_USERNAME']
        msg['To'] = config['SMTP_USERNAME']  # Send to yourself for testing
        msg['Subject'] = f"Lab Maintenance System - Test Email ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        
        body = f"""
        This is a test email from the Lab Maintenance System.
        
        ✅ Email configuration is working correctly!
        
        Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        You can now implement email reminders in the main application.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox: {config['SMTP_USERNAME']}")
        print()
        print("🎉 Email configuration is ready for use!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed!")
        print("   - Check your username and app password")
        print("   - Make sure 2FA is enabled and you're using an app password")
        return False
        
    except smtplib.SMTPConnectError:
        print("❌ Connection failed!")
        print("   - Check your SMTP server and port")
        print("   - Verify internet connection")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_email_config()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you've updated email_reminders.env with real credentials")
        print("2. Verify you're using an app password (not regular password)")
        print("3. Check that 2FA is enabled on the email account")
        print("4. Ensure the email account exists and is active")
        sys.exit(1)
    else:
        print("\n🚀 Ready to implement email reminders!") 