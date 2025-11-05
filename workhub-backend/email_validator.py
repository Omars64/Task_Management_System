# workhub-backend/email_validator.py
"""
Real-world email validation module
Checks if email domains are valid and can receive emails
"""
import re
import dns.resolver
from typing import Dict, Tuple

# List of known disposable/temporary email domains
DISPOSABLE_EMAIL_DOMAINS = {
    'tempmail.com', 'guerrillamail.com', '10minutemail.com', 'throwaway.email',
    'mailinator.com', 'maildrop.cc', 'temp-mail.org', 'yopmail.com',
    'fakeinbox.com', 'trashmail.com', 'getnada.com', 'emailondeck.com',
    'sharklasers.com', 'guerrillamail.info', 'grr.la', 'spam4.me',
    'mailnesia.com', 'mintemail.com', 'spamgourmet.com', 'mytemp.email',
    '33mail.com', 'mailcatch.com', 'getairmail.com', 'dispostable.com',
}

# Common typos in popular domains
COMMON_DOMAIN_TYPOS = {
    'gmial.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gmil.com': 'gmail.com',
    'yahou.com': 'yahoo.com',
    'yaho.com': 'yahoo.com',
    'hotmial.com': 'hotmail.com',
    'hotmai.com': 'hotmail.com',
    'outlok.com': 'outlook.com',
}


class EmailValidator:
    """Advanced email validation including real-world checks"""
    
    @staticmethod
    def validate_email_format(email: str) -> Tuple[bool, str]:
        """Basic format validation"""
        if not email or not isinstance(email, str):
            return False, "Email is required"
        
        email = email.strip().lower()
        
        # RFC 5322 compliant regex (simplified)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for multiple @ signs
        if email.count('@') != 1:
            return False, "Email must contain exactly one @ symbol"
        
        # Split email into local and domain parts
        local, domain = email.split('@')
        
        # Validate local part (before @)
        if len(local) == 0 or len(local) > 64:
            return False, "Email username must be 1-64 characters"
        
        # Validate domain part
        if len(domain) == 0 or len(domain) > 255:
            return False, "Email domain is invalid"
        
        # Check for consecutive dots
        if '..' in email:
            return False, "Email cannot contain consecutive dots"
        
        # Check if starts or ends with dot
        if local.startswith('.') or local.endswith('.'):
            return False, "Email username cannot start or end with a dot"
        
        return True, email
    
    @staticmethod
    def check_disposable_email(email: str) -> Tuple[bool, str]:
        """Check if email is from a disposable/temporary email service"""
        domain = email.split('@')[1].lower()
        
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            return False, f"Disposable email addresses from {domain} are not allowed"
        
        return True, ""
    
    @staticmethod
    def check_domain_typo(email: str) -> Tuple[bool, str, str]:
        """Check for common domain typos and suggest corrections"""
        domain = email.split('@')[1].lower()
        
        if domain in COMMON_DOMAIN_TYPOS:
            suggested_domain = COMMON_DOMAIN_TYPOS[domain]
            local = email.split('@')[0]
            suggested_email = f"{local}@{suggested_domain}"
            return False, f"Did you mean {suggested_email}?", suggested_email
        
        return True, "", ""
    
    @staticmethod
    def check_mx_records(email: str) -> Tuple[bool, str]:
        """
        Check if domain has valid MX (Mail Exchange) records
        This verifies the domain can actually receive emails
        """
        domain = email.split('@')[1]
        
        try:
            # Query MX records for the domain
            mx_records = dns.resolver.resolve(domain, 'MX')
            
            if not mx_records:
                return False, f"Domain {domain} cannot receive emails (no MX records)"
            
            # Domain has MX records and can receive emails
            return True, ""
            
        except dns.resolver.NXDOMAIN:
            return False, f"Domain {domain} does not exist"
        
        except dns.resolver.NoAnswer:
            return False, f"Domain {domain} has no mail server configured"
        
        except dns.resolver.Timeout:
            # Don't block on timeout, might be temporary network issue
            return True, ""
        
        except Exception as e:
            # Don't block on other errors, allow through
            print(f"MX check error for {email}: {str(e)}")
            return True, ""
    
    @staticmethod
    def validate_email_comprehensive(email: str, check_mx: bool = True) -> Dict:
        """
        Comprehensive email validation
        
        Args:
            email: Email address to validate
            check_mx: Whether to check MX records (can be slow, set False for faster validation)
        
        Returns:
            Dict with validation results
        """
        result = {
            'valid': False,
            'email': email,
            'normalized_email': '',
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Step 1: Format validation
        is_valid, normalized = EmailValidator.validate_email_format(email)
        if not is_valid:
            result['errors'].append(normalized)
            return result
        
        result['normalized_email'] = normalized
        
        # Step 2: Check for disposable emails
        is_valid, error = EmailValidator.check_disposable_email(normalized)
        if not is_valid:
            result['errors'].append(error)
            return result
        
        # Step 3: Check for domain typos
        is_valid, suggestion, suggested_email = EmailValidator.check_domain_typo(normalized)
        if not is_valid:
            result['warnings'].append(suggestion)
            result['suggestions'].append(suggested_email)
            # Don't return here, just warn
        
        # Step 4: Check MX records (optional, can be slow)
        if check_mx:
            is_valid, error = EmailValidator.check_mx_records(normalized)
            if not is_valid:
                result['errors'].append(error)
                return result
        
        # All checks passed
        result['valid'] = True
        return result


# Singleton instance
email_validator = EmailValidator()

