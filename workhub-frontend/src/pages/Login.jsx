import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ValidationUtils } from '../utils/validation';
import { useDebounce } from '../hooks/useDebounce';
import { authAPI } from '../services/api';
import { PasswordStrength } from '../components/PasswordStrength';
import './Login.css';

const Login = () => {
  const [mode, setMode] = useState('login'); // 'login', 'signup', 'verify'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [errors, setErrors] = useState({});
  const [warnings, setWarnings] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [accountStatus, setAccountStatus] = useState(null); // {exists, email_verified, signup_status}
  const [loading, setLoading] = useState(false);
  const [validatingEmail, setValidatingEmail] = useState(false);
  const [touched, setTouched] = useState({});
  const [signupUserId, setSignupUserId] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Debounced email for real-time validation (only validate after user stops typing)
  const debouncedEmail = useDebounce(email, 800);

  // Real-time email validation (debounced) - checks real-world email validity
  useEffect(() => {
    if (debouncedEmail && touched.email && mode === 'signup') {
      validateEmailRealtime(debouncedEmail);
    }
  }, [debouncedEmail, mode]);

  // Account status hint on Login as user types email
  useEffect(() => {
    const run = async () => {
      if (mode !== 'login') { setAccountStatus(null); return; }
      const val = debouncedEmail?.trim();
      if (!val) { setAccountStatus(null); return; }
      // Basic format check before hitting API
      const basic = ValidationUtils.validateEmail(val);
      if (!basic.isValid) { setAccountStatus(null); return; }
      try {
        const res = await authAPI.checkAccountStatus(val);
        setAccountStatus(res.data || null);
      } catch {
        setAccountStatus(null);
      }
    };
    run();
  }, [debouncedEmail, mode]);

  const validateEmailRealtime = async (emailValue) => {
    setValidatingEmail(true);
    
    try {
      // First do basic format validation
      const formatResult = ValidationUtils.validateEmail(emailValue);
      if (!formatResult.isValid) {
        setErrors(prev => ({ ...prev, email: formatResult.message }));
        setValidatingEmail(false);
        return false;
      }
      
      // Check if email already exists
      const existsResponse = await authAPI.checkEmailExists(emailValue);
      if (existsResponse.data.exists) {
        setErrors(prev => ({ ...prev, email: existsResponse.data.message }));
        setValidatingEmail(false);
        return false;
      }
      
      // Then check real-world validity (MX records, disposable emails, etc.)
      const response = await authAPI.validateEmail(emailValue, true);
      const result = response.data;
      
      if (!result.valid) {
        setErrors(prev => ({ ...prev, email: result.errors[0] || 'Invalid email' }));
        setValidatingEmail(false);
        return false;
      }
      
      // Check for warnings (typos, suggestions)
      if (result.warnings && result.warnings.length > 0) {
        setWarnings(prev => ({ ...prev, email: result.warnings[0] }));
      } else {
        setWarnings(prev => {
          const newWarnings = { ...prev };
          delete newWarnings.email;
          return newWarnings;
        });
      }
      
      // Email is valid
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.email;
        return newErrors;
      });
      setValidatingEmail(false);
      return true;
      
    } catch (err) {
      setValidatingEmail(false);
      return false;
    }
  };

  const validateField = (field, value) => {
    let result;
    switch (field) {
      case 'name':
        if (!value || value.trim().length < 2) {
          result = { isValid: false, message: 'Name must be at least 2 characters' };
        } else if (!/^[A-Za-z\s\-']{2,50}$/.test(value)) {
          result = { isValid: false, message: 'Name can only contain letters, spaces, hyphens, and apostrophes' };
        } else {
          result = { isValid: true };
        }
        break;
      case 'email':
        result = ValidationUtils.validateEmail(value);
        break;
      case 'password':
        if (!value) {
          result = { isValid: false, message: 'Password is required' };
        } else if (value.length < 10) {
          result = { isValid: false, message: 'Password must be at least 10 characters' };
        } else {
          // Check password strength
          let charClasses = 0;
          if (/[A-Z]/.test(value)) charClasses++;
          if (/[a-z]/.test(value)) charClasses++;
          if (/\d/.test(value)) charClasses++;
          if (/[^A-Za-z0-9]/.test(value)) charClasses++;
          
          if (charClasses < 3) {
            result = { isValid: false, message: 'Password must include at least 3 of: uppercase, lowercase, digit, special character' };
          } else {
            result = { isValid: true };
          }
        }
        break;
      case 'confirmPassword':
        if (mode === 'signup' && value !== password) {
          result = { isValid: false, message: 'Passwords do not match' };
        } else {
          result = { isValid: true };
        }
        break;
      case 'verificationCode':
        if (!value || value.length !== 6 || !/^\d{6}$/.test(value)) {
          result = { isValid: false, message: 'Verification code must be 6 digits' };
        } else {
          result = { isValid: true };
        }
        break;
      default:
        result = { isValid: true };
    }

    if (!result.isValid) {
      setErrors(prev => ({ ...prev, [field]: result.message }));
      return false;
    } else {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
      return true;
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Mark all fields as touched
    setTouched({ email: true, password: true });

    // Validate all fields
    const emailValid = validateField('email', email);
    const passwordValid = validateField('password', password);

    if (!emailValid || !passwordValid) {
      return;
    }

    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Mark all fields as touched
    setTouched({ name: true, email: true, password: true, confirmPassword: true });

    // Validate all fields
    const nameValid = validateField('name', name);
    const emailValid = validateField('email', email);
    const passwordValid = validateField('password', password);
    const confirmValid = validateField('confirmPassword', confirmPassword);

    if (!nameValid || !emailValid || !passwordValid || !confirmValid) {
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.signup({
        name,
        email,
        password,
        confirm: confirmPassword
      });

      setSignupUserId(response.data.user_id);
      
      // SECURITY: Verification code is NEVER in response - only sent via email
      // Show appropriate message based on email_sent status
      if (response.data.email_sent) {
        setSuccess("Signup successful! Please check your email for the verification code.");
      } else {
        setSuccess("Signup successful! Verification code has been generated. Please check server logs for the code (email not configured).");
      }
      
      setMode('verify');
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validate code
    const codeValid = validateField('verificationCode', verificationCode);
    if (!codeValid) {
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.verifyEmail(email, verificationCode);
      setSuccess('Email verified successfully! Your account is pending admin approval. You will receive an email when approved.');
      
      // Clear form and switch to login after a delay so the user can read the message
      setTimeout(() => {
        setMode('login');
        setName('');
        setPassword('');
        setConfirmPassword('');
        setVerificationCode('');
        setTouched({});
        setErrors({});
        setWarnings({});
        setSuccess('');
      }, 5000);
    } catch (err) {
      setError(err.response?.data?.error || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await authAPI.resendVerification(email);
      
      // SECURITY: Verification code is NEVER in response - only sent via email
      // Show appropriate message based on email_sent status
      if (response.data.email_sent) {
        setSuccess("Verification code sent to your email!");
      } else {
        setSuccess("Verification code generated. Please check server logs for the code (email not configured).");
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to resend code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBlur = (field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    const value = { email, password, name, confirmPassword, verificationCode }[field];
    validateField(field, value);
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setError('');
    setSuccess('');
    setErrors({});
    setWarnings({});
    setTouched({});
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">Work Hub</h1>
          <p className="login-subtitle">Task Management System</p>
        </div>

        {/* Mode Tabs */}
        {mode !== 'verify' && (
          <div className="mode-tabs">
            <button
              className={`mode-tab ${mode === 'login' ? 'active' : ''}`}
              onClick={() => switchMode('login')}
              type="button"
            >
              Login
            </button>
            <button
              className={`mode-tab ${mode === 'signup' ? 'active' : ''}`}
              onClick={() => switchMode('signup')}
              type="button"
            >
              Sign Up
            </button>
          </div>
        )}

        {/* Alert Messages */}
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Login Form */}
        {mode === 'login' && (
          <form className="login-form" onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                className={`form-input ${errors.email && touched.email ? 'has-error' : ''}`}
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.email;
                      return newErrors;
                    });
                  }
                }}
                onBlur={() => handleBlur('email')}
                placeholder="Enter your email"
                autoComplete="email"
              />
              {errors.email && touched.email && (
                <div className="form-error">{errors.email}</div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className={`form-input ${errors.password && touched.password ? 'has-error' : ''}`}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.password;
                      return newErrors;
                    });
                  }
                }}
                onBlur={() => handleBlur('password')}
                placeholder="Enter your password"
                autoComplete="current-password"
              />
              {errors.password && touched.password && (
                <div className="form-error">{errors.password}</div>
              )}
            </div>

            <button 
              type="submit" 
              className="btn btn-primary w-full" 
              disabled={loading || Object.keys(errors).length > 0}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
            
            <div style={{ textAlign: 'center', marginTop: '15px' }}>
              <Link 
                to="/forgot-password" 
                style={{ 
                  color: '#68939d', 
                  textDecoration: 'none', 
                  fontSize: '14px' 
                }}
              >
                Forgot your password?
              </Link>
            </div>
          </form>
        )}

        {/* Signup Form */}
        {mode === 'signup' && (
          <form className="login-form" onSubmit={handleSignupSubmit}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className={`form-input ${errors.name && touched.name ? 'has-error' : ''}`}
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (errors.name) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.name;
                      return newErrors;
                    });
                  }
                }}
                onBlur={() => handleBlur('name')}
                placeholder="Enter your full name"
                autoComplete="name"
              />
              {errors.name && touched.name && (
                <div className="form-error">{errors.name}</div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                Email
                {validatingEmail && <span className="validating-indicator"> (checking...)</span>}
              </label>
              <input
                type="email"
                className={`form-input ${errors.email && touched.email ? 'has-error' : ''} ${warnings.email && touched.email ? 'has-warning' : ''}`}
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.email;
                      return newErrors;
                    });
                  }
                  if (warnings.email) {
                    setWarnings(prev => {
                      const newWarnings = { ...prev };
                      delete newWarnings.email;
                      return newWarnings;
                    });
                  }
                }}
                onBlur={() => handleBlur('email')}
                placeholder="Enter your email"
                autoComplete="email"
              />
              {errors.email && touched.email && (
                <div className="form-error">{errors.email}</div>
              )}
              {warnings.email && touched.email && !errors.email && (
                <div className="form-warning">{warnings.email}</div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className={`form-input ${errors.password && touched.password ? 'has-error' : ''}`}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.password;
                      return newErrors;
                    });
                  }
                }}
                onBlur={() => handleBlur('password')}
                placeholder="Create a strong password"
                autoComplete="new-password"
              />
              {errors.password && touched.password && (
                <div className="form-error">{errors.password}</div>
              )}
              {password && <PasswordStrength password={password} />}
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                className={`form-input ${errors.confirmPassword && touched.confirmPassword ? 'has-error' : ''}`}
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (errors.confirmPassword) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.confirmPassword;
                      return newErrors;
                    });
                  }
                }}
                onBlur={() => handleBlur('confirmPassword')}
                placeholder="Confirm your password"
                autoComplete="new-password"
              />
              {errors.confirmPassword && touched.confirmPassword && (
                <div className="form-error">{errors.confirmPassword}</div>
              )}
            </div>

            <div className="signup-info">
              <p>✓ You will receive a verification code via email</p>
              <p>✓ Admin approval required to access the system</p>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary w-full" 
              disabled={loading || Object.keys(errors).length > 0 || validatingEmail}
            >
              {loading ? 'Creating Account...' : 'Sign Up'}
            </button>
          </form>
        )}

        {/* Verification Form */}
        {mode === 'verify' && (
          <form className="login-form" onSubmit={handleVerifySubmit}>
            <div className="verify-header">
              <h3>Verify Your Email</h3>
              <p>We've sent a 6-digit verification code to:</p>
              <p className="verify-email">{email}</p>
            </div>

            <div className="form-group">
              <label className="form-label">Verification Code</label>
              <input
                type="text"
                className={`form-input verification-input ${errors.verificationCode ? 'has-error' : ''}`}
                value={verificationCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setVerificationCode(value);
                  if (errors.verificationCode) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.verificationCode;
                      return newErrors;
                    });
                  }
                }}
                placeholder="000000"
                maxLength={6}
                autoComplete="off"
              />
              {errors.verificationCode && (
                <div className="form-error">{errors.verificationCode}</div>
              )}
            </div>

            <button 
              type="submit" 
              className="btn btn-primary w-full" 
              disabled={loading || verificationCode.length !== 6}
            >
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>

            <div className="resend-section">
              <p>Didn't receive the code?</p>
              <button
                type="button"
                className="btn-link"
                onClick={handleResendCode}
                disabled={loading}
              >
                Resend Code
              </button>
            </div>

            <button
              type="button"
              className="btn-link"
              onClick={() => switchMode('signup')}
            >
              ← Back to Signup
            </button>
          </form>
        )}

        {mode === 'login' && (
          <div className="login-footer">
            {accountStatus && accountStatus.exists && accountStatus.signup_status === 'pending' && (
              <div className="hint-box hint-pending">
                Your account is awaiting admin approval.
              </div>
            )}
            {accountStatus && accountStatus.exists && accountStatus.signup_status === 'rejected' && (
              <div className="hint-box hint-rejected">
                Your signup was rejected. Please contact support.
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Styles */}
      <style jsx>{`
        .mode-tabs {
          display: flex;
          gap: 0;
          margin-bottom: 24px;
          border-bottom: 2px solid #e5e7eb;
        }
        
        .mode-tab {
          flex: 1;
          padding: 12px 24px;
          background: none;
          border: none;
          border-bottom: 2px solid transparent;
          color: #6b7280;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: -2px;
        }
        
        .mode-tab:hover {
          color: #68939d;
        }
        
        .mode-tab.active {
          color: #68939d;
          border-bottom-color: #68939d;
        }
        
        .alert {
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 14px;
        }
        
        .alert-error {
          background-color: #fef2f2;
          border: 1px solid #fecaca;
          color: #dc2626;
        }
        
        .alert-success {
          background-color: #f0fdf4;
          border: 1px solid #bbf7d0;
          color: #16a34a;
        }
        .hint-box {
          margin-top: 16px;
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 14px;
        }
        .hint-pending {
          background: #fffbeb;
          border: 1px solid #fde68a;
          color: #92400e;
        }
        .hint-rejected {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #991b1b;
        }
        
        .form-error {
          color: #dc2626;
          font-size: 0.875rem;
          margin-top: 4px;
          display: block;
          animation: slideIn 0.2s ease-out;
        }
        
        .form-warning {
          color: #f59e0b;
          font-size: 0.875rem;
          margin-top: 4px;
          display: block;
          animation: slideIn 0.2s ease-out;
        }
        
        .form-input.has-error {
          border-color: #dc2626;
          background-color: #fef2f2;
        }
        
        .form-input.has-warning {
          border-color: #f59e0b;
          background-color: #fffbeb;
        }
        
        .form-input.has-error:focus {
          outline: none;
          border-color: #dc2626;
          box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
        }
        
        .form-input.has-warning:focus {
          outline: none;
          border-color: #f59e0b;
          box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
        }
        
        .validating-indicator {
          font-size: 0.8125rem;
          color: #6b7280;
          font-weight: 400;
          font-style: italic;
          animation: pulse 1.5s ease-in-out infinite;
        }
        
        .signup-info {
          background-color: #f0f9ff;
          border: 1px solid #bae6fd;
          border-radius: 8px;
          padding: 12px;
          margin: 16px 0;
        }
        
        .signup-info p {
          margin: 4px 0;
          font-size: 0.875rem;
          color: #0369a1;
        }
        
        .verify-header {
          text-align: center;
          margin-bottom: 24px;
        }
        
        .verify-header h3 {
          color: #111827;
          margin-bottom: 8px;
        }
        
        .verify-header p {
          color: #6b7280;
          font-size: 0.875rem;
          margin: 4px 0;
        }
        
        .verify-email {
          color: #68939d !important;
          font-weight: 600;
          font-size: 1rem !important;
        }
        
        .verification-input {
          text-align: center;
          font-size: 24px;
          letter-spacing: 8px;
          font-weight: 600;
        }
        
        .resend-section {
          text-align: center;
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
        }
        
        .resend-section p {
          color: #6b7280;
          font-size: 0.875rem;
          margin-bottom: 8px;
        }
        
        .btn-link {
          background: none;
          border: none;
          color: #68939d;
          cursor: pointer;
          font-weight: 500;
          padding: 8px;
          font-size: 0.875rem;
        }
        
        .btn-link:hover {
          color: #4338ca;
          text-decoration: underline;
        }
        
        .btn-link:disabled {
          color: #9ca3af;
          cursor: not-allowed;
        }
        
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
};

export default Login;
