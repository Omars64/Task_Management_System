import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import './Login.css';
import { PasswordStrength } from '../components/PasswordStrength';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [touched, setTouched] = useState({});
  
  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    if (!newPassword || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.resetPassword(token, newPassword);
      
      setMessage(response.data.message || 'Password reset successful! Redirecting to login...');
      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      // Log the error for debugging
      console.error('Password reset error:', err);
      console.error('Error response:', err.response?.data);
      
      // Show more specific error messages
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to reset password. Please try again.';
      setError(errorMsg);
    } finally {
      setLoading(false)
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h1 className="login-title">Reset Password</h1>
        <p className="login-subtitle">Enter your new password</p>

        {error && <div className="alert alert-error">{error}</div>}
        {message && <div className="alert alert-success">{message}</div>}

        {token ? (
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <input
                type="password"
                id="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                required
                disabled={loading}
                onBlur={() => setTouched(prev => ({ ...prev, password: true }))}
              />
              {newPassword && <PasswordStrength password={newPassword} />}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                required
                disabled={loading}
                onBlur={() => setTouched(prev => ({ ...prev, confirm: true }))}
              />
              {confirmPassword && newPassword !== confirmPassword && touched.confirm && (
                <div className="form-error">Passwords do not match</div>
              )}
            </div>

            <button type="submit" className="btn btn-primary w-full" disabled={loading}>
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        ) : (
          <div className="login-form">
            <p style={{ textAlign: 'center', color: '#666' }}>
              No reset token provided. Please click the link from your email.
            </p>
            <Link to="/forgot-password" className="login-button" style={{ display: 'block', textAlign: 'center', marginTop: '20px' }}>
              Request New Reset Link
            </Link>
          </div>
        )}

        <div className="login-footer">
          <Link to="/login">Back to Login</Link>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;

