"""
Email verification module (P0):
- Generate verification tokens with 24h expiry
- Send verification emails
- Verify tokens
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from flask import url_for
from flask_mail import Message


# In-memory token storage (for production, use Redis or database)
# Format: {token: {'email': str, 'expires_at': datetime, 'purpose': str}}
verification_tokens = {}


class EmailVerification:
    """Email verification service (P0)"""
    
    TOKEN_EXPIRY_HOURS = 24
    
    @staticmethod
    def generate_token(email: str, purpose: str = 'verify_email') -> str:
        """
        Generate a secure verification token with 24h expiry (P0).
        
        Args:
            email: User email address
            purpose: Token purpose (verify_email, reset_password, etc.)
        
        Returns:
            Secure token string
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Store token with metadata
        expires_at = datetime.now(timezone.utc) + timedelta(hours=EmailVerification.TOKEN_EXPIRY_HOURS)
        verification_tokens[token] = {
            'email': email.lower(),
            'expires_at': expires_at,
            'purpose': purpose,
            'created_at': datetime.now(timezone.utc)
        }
        
        return token
    
    @staticmethod
    def verify_token(token: str, purpose: str = 'verify_email') -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify email verification token.
        
        Args:
            token: Token to verify
            purpose: Expected token purpose
        
        Returns:
            Tuple of (is_valid, email, error_message)
        """
        if not token or token not in verification_tokens:
            return False, None, "Invalid or expired verification token."
        
        token_data = verification_tokens[token]
        
        # Check expiry
        if datetime.now(timezone.utc) > token_data['expires_at']:
            # Clean up expired token
            del verification_tokens[token]
            return False, None, "Verification token has expired. Please request a new one."
        
        # Check purpose
        if token_data['purpose'] != purpose:
            return False, None, "Invalid verification token."
        
        email = token_data['email']
        
        # Token is valid - delete it (one-time use)
        del verification_tokens[token]
        
        return True, email, None
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from storage"""
        now = datetime.now(timezone.utc)
        expired_tokens = [
            token for token, data in verification_tokens.items()
            if now > data['expires_at']
        ]
        
        for token in expired_tokens:
            del verification_tokens[token]
        
        return len(expired_tokens)
    
    @staticmethod
    def send_verification_email(mail, email: str, token: str, base_url: str = None):
        """
        Send verification email to user (P0).
        
        Args:
            mail: Flask-Mail instance
            email: Recipient email
            token: Verification token
            base_url: Base URL for verification link
        """
        if not base_url:
            base_url = "http://localhost:3000"  # Default for development
        
        verification_link = f"{base_url}/verify-email?token={token}"
        
        msg = Message(
            subject="Verify Your Email - WorkHub Task Management",
            recipients=[email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #4CAF50;">Welcome to WorkHub!</h2>
                        <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}" 
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Verify Email Address
                            </a>
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            This link will expire in 24 hours. If you didn't create an account, 
                            please ignore this email.
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            Or copy and paste this link into your browser:<br>
                            <span style="color: #4CAF50;">{verification_link}</span>
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            WorkHub Task Management System<br>
                            This is an automated email, please do not reply.
                        </p>
                    </div>
                </body>
            </html>
            """,
            body=f"""
            Welcome to WorkHub!
            
            Thank you for registering. Please verify your email address by visiting this link:
            
            {verification_link}
            
            This link will expire in 24 hours. If you didn't create an account, please ignore this email.
            
            ---
            WorkHub Task Management System
            """
        )
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(mail, email: str, token: str, base_url: str = None):
        """
        Send password reset email (P0).
        
        Args:
            mail: Flask-Mail instance
            email: Recipient email
            token: Reset token
            base_url: Base URL for reset link
        """
        if not base_url:
            base_url = "http://localhost:3000"
        
        reset_link = f"{base_url}/reset-password?token={token}"
        
        msg = Message(
            subject="Reset Your Password - WorkHub",
            recipients=[email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #FF9800;">Password Reset Request</h2>
                        <p>We received a request to reset your password. Click the link below to create a new password:</p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" 
                               style="background-color: #FF9800; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Reset Password
                            </a>
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            This link will expire in 24 hours. If you didn't request a password reset, 
                            please ignore this email and your password will remain unchanged.
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            Or copy and paste this link into your browser:<br>
                            <span style="color: #FF9800;">{reset_link}</span>
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            WorkHub Task Management System<br>
                            This is an automated email, please do not reply.
                        </p>
                    </div>
                </body>
            </html>
            """,
            body=f"""
            Password Reset Request
            
            We received a request to reset your password. Visit this link to create a new password:
            
            {reset_link}
            
            This link will expire in 24 hours. If you didn't request a password reset, 
            please ignore this email and your password will remain unchanged.
            
            ---
            WorkHub Task Management System
            """
        )
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False


# Convenience instance
email_verification = EmailVerification()

