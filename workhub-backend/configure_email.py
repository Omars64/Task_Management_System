#!/usr/bin/env python3
"""
Script to configure email settings in SystemSettings database
Usage: python configure_email.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, SystemSettings

def configure_email():
    """Configure email settings in SystemSettings"""
    app = create_app()
    
    with app.app_context():
        # Get or create SystemSettings
        settings = SystemSettings.query.first()
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
            db.session.commit()
        
        # Get email configuration from environment variables or prompt user
        print("=" * 60)
        print("Email Configuration Setup")
        print("=" * 60)
        print()
        
        # Check if env vars are set
        smtp_server = os.environ.get('MAIL_SERVER') or os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('MAIL_PORT') or os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('MAIL_USERNAME') or os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('MAIL_PASSWORD') or os.environ.get('SMTP_PASSWORD', '')
        smtp_from_email = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('SMTP_FROM_EMAIL', '')
        smtp_from_name = os.environ.get('SMTP_FROM_NAME', 'WorkHub Task Management')
        
        # If not in env vars, check existing settings
        if not smtp_username:
            smtp_username = settings.smtp_username or ''
        if not smtp_password:
            smtp_password = settings.smtp_password or ''
        if not smtp_from_email:
            smtp_from_email = settings.smtp_from_email or ''
        
        # Prompt for missing values
        if not smtp_username:
            smtp_username = input("Enter SMTP username (email): ").strip()
        else:
            print(f"SMTP Username: {smtp_username}")
        
        if not smtp_password:
            smtp_password = input("Enter SMTP password (app password): ").strip()
        else:
            print(f"SMTP Password: {'*' * len(smtp_password)}")
        
        if not smtp_from_email:
            smtp_from_email = input(f"Enter sender email (default: {smtp_username}): ").strip() or smtp_username
        
        # Update settings
        settings.smtp_server = smtp_server
        settings.smtp_port = smtp_port
        settings.smtp_username = smtp_username
        settings.smtp_password = smtp_password
        settings.smtp_from_email = smtp_from_email
        settings.smtp_from_name = smtp_from_name
        settings.email_notifications_enabled = True
        
        try:
            db.session.commit()
            print()
            print("=" * 60)
            print("✓ Email configuration saved successfully!")
            print("=" * 60)
            print(f"SMTP Server: {smtp_server}")
            print(f"SMTP Port: {smtp_port}")
            print(f"SMTP Username: {smtp_username}")
            print(f"From Email: {smtp_from_email}")
            print(f"From Name: {smtp_from_name}")
            print()
            print("The application will now use these settings for sending emails.")
            print("You may need to restart the application for changes to take effect.")
            print("=" * 60)
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error saving email configuration: {e}")
            return False

if __name__ == '__main__':
    try:
        configure_email()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

