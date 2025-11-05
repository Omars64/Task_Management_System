import React from 'react';

/**
 * PasswordStrength Component
 * Displays visual feedback for password strength with bar and suggestions
 */
export const PasswordStrength = ({ password, showDetails = true }) => {
  const calculateStrength = (pwd) => {
    if (!pwd) return { strength: 'none', score: 0, color: '#e5e7eb', text: '', feedback: [] };
    
    let score = 0;
    let feedback = [];
    
    // Length check (Enhanced: 10 chars minimum per P0 requirements)
    if (pwd.length >= 12) score += 2;
    else if (pwd.length >= 10) score += 1;
    else feedback.push('Use at least 10 characters');
    
    // Character variety - need at least 3 of 4 classes
    if (/[A-Z]/.test(pwd)) score++;
    else feedback.push('Add uppercase letters');
    
    if (/[a-z]/.test(pwd)) score++;
    else feedback.push('Add lowercase letters');
    
    if (/\d/.test(pwd)) score++;
    else feedback.push('Add numbers');
    
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    else feedback.push('Add special characters');
    
    // Check for common patterns
    if (/(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)/i.test(pwd)) {
      score = Math.max(0, score - 2);
      feedback.push('Avoid sequential patterns');
    }
    
    // Determine strength level
    if (score <= 2) return { strength: 'weak', score: score * 20, color: '#ef4444', text: 'Weak', feedback };
    if (score <= 4) return { strength: 'fair', score: score * 20, color: '#f59e0b', text: 'Fair', feedback };
    if (score <= 6) return { strength: 'good', score: score * 15, color: '#10b981', text: 'Good', feedback };
    return { strength: 'strong', score: 100, color: '#059669', text: 'Strong', feedback: [] };
  };
  
  const strength = calculateStrength(password);
  
  if (!password) return null;
  
  return (
    <div className="password-strength">
      <div className="strength-bar-container">
        <div 
          className="strength-bar" 
          style={{ 
            width: `${strength.score}%`, 
            backgroundColor: strength.color,
            height: '4px',
            borderRadius: '2px',
            transition: 'all 0.3s ease'
          }} 
        />
      </div>
      {showDetails && (
        <div className="strength-info">
          <span className="strength-text" style={{ color: strength.color, fontWeight: 600 }}>
            {strength.text}
          </span>
          {strength.feedback.length > 0 && (
            <span className="strength-feedback">
              {strength.feedback[0]}
            </span>
          )}
        </div>
      )}
      
      <style jsx>{`
        .password-strength {
          margin-top: 8px;
        }
        .strength-bar-container {
          width: 100%;
          height: 4px;
          background-color: #e5e7eb;
          border-radius: 2px;
          overflow: hidden;
        }
        .strength-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 6px;
          font-size: 0.875rem;
          gap: 8px;
        }
        .strength-feedback {
          color: #6b7280;
          font-size: 0.8125rem;
        }
        @media (max-width: 640px) {
          .strength-info {
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
          }
        }
      `}</style>
    </div>
  );
};

export default PasswordStrength;

