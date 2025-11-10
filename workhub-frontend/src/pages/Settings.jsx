import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { settingsAPI, usersAPI, notificationsAPI } from '../services/api';

const Settings = () => {
  const { user, isAdmin, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('personal');
  const [personalSettings, setPersonalSettings] = useState({
    theme: 'light',
    language: 'en',
    notifications_enabled: true
  });
  const [systemSettings, setSystemSettings] = useState({
    site_title: '',
    default_role: 'user',
    email_notifications_enabled: true,
    default_language: 'en'
  });
  const [notificationPrefs, setNotificationPrefs] = useState({
    email_task_assigned: true,
    email_task_updated: true,
    email_task_commented: true,
    email_task_due_soon: true,
    email_task_overdue: true,
    inapp_task_assigned: true,
    inapp_task_updated: true,
    inapp_task_commented: true,
    inapp_task_due_soon: true,
    inapp_task_overdue: true,
    daily_digest: false,
    weekly_digest: false
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const personalRes = await settingsAPI.getPersonal();
      setPersonalSettings(personalRes.data);
      
      // Fetch notification preferences
      try {
        const prefsRes = await notificationsAPI.getPreferences();
        setNotificationPrefs(prefsRes.data);
      } catch (error) {
        console.error('Failed to fetch notification preferences:', error);
      }
      
      if (isAdmin()) {
        const systemRes = await settingsAPI.getSystem();
        setSystemSettings(systemRes.data);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const validatePersonalSettings = () => {
    const newErrors = {};
    
    // Validate theme
    if (!['light', 'dark'].includes(personalSettings.theme)) {
      newErrors.theme = 'Theme must be either light or dark';
    }
    
    // Validate language
    if (!['en', 'es', 'fr'].includes(personalSettings.language)) {
      newErrors.language = 'Invalid language selection';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateSystemSettings = () => {
    const newErrors = {};
    
    // Validate site title
    if (systemSettings.site_title) {
      const trimmed = systemSettings.site_title.trim();
      if (trimmed.length < 2) {
        newErrors.site_title = 'Site title must be at least 2 characters';
      } else if (trimmed.length > 100) {
        newErrors.site_title = 'Site title must be less than 100 characters';
      }
    }
    
    // Validate default role
    if (!['user', 'admin'].includes(systemSettings.default_role)) {
      newErrors.default_role = 'Default role must be either user or admin';
    }
    
    // Validate default language
    if (!['en', 'es', 'fr'].includes(systemSettings.default_language)) {
      newErrors.default_language = 'Invalid language selection';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePersonalSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setErrors({});
    
    if (!validatePersonalSettings()) {
      return;
    }
    
    try {
      await settingsAPI.updatePersonal(personalSettings);
      
      // Update user in context
      const updatedUser = await usersAPI.getById(user.id);
      updateUser(updatedUser.data);
      
      setMessage('Personal settings updated successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Failed to update personal settings');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleSystemSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setErrors({});
    
    if (!validateSystemSettings()) {
      return;
    }
    
    try {
      await settingsAPI.updateSystem(systemSettings);
      setMessage('System settings updated successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Failed to update system settings');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleNotificationPrefsSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    try {
      await notificationsAPI.updatePreferences(notificationPrefs);
      setMessage('Notification preferences updated successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Failed to update notification preferences');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      <div className="card">
        <div style={{ borderBottom: '1px solid var(--border-color)', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '24px' }}>
            <button
              onClick={() => setActiveTab('personal')}
              style={{
                padding: '12px 0',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'personal' ? '2px solid var(--primary-color)' : 'none',
                color: activeTab === 'personal' ? 'var(--primary-color)' : 'var(--text-light)',
                cursor: 'pointer',
                fontWeight: 500
              }}
            >
              Personal Settings
            </button>
            <button
              onClick={() => setActiveTab('notifications')}
              style={{
                padding: '12px 0',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'notifications' ? '2px solid var(--primary-color)' : 'none',
                color: activeTab === 'notifications' ? 'var(--primary-color)' : 'var(--text-light)',
                cursor: 'pointer',
                fontWeight: 500
              }}
            >
              Notification Preferences
            </button>
            {isAdmin() && (
              <button
                onClick={() => setActiveTab('system')}
                style={{
                  padding: '12px 0',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'system' ? '2px solid var(--primary-color)' : 'none',
                  color: activeTab === 'system' ? 'var(--primary-color)' : 'var(--text-light)',
                  cursor: 'pointer',
                  fontWeight: 500
                }}
              >
                System Settings
              </button>
            )}
          </div>
        </div>

        {message && <div className="alert alert-success">{message}</div>}

        {activeTab === 'personal' && (
          <form onSubmit={handlePersonalSubmit}>
            <div className="form-group">
              <label className="form-label">Theme</label>
              <select
                className={`form-select ${errors.theme ? 'has-error' : ''}`}
                value={personalSettings.theme}
                onChange={(e) => {
                  setPersonalSettings({ ...personalSettings, theme: e.target.value });
                  // Clear error when user changes
                  if (errors.theme) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.theme;
                      return newErrors;
                    });
                  }
                }}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
              {errors.theme && <div className="form-error">{errors.theme}</div>}
            </div>
            <div className="form-group">
              <label className="form-label">Language</label>
              <select
                className={`form-select ${errors.language ? 'has-error' : ''}`}
                value={personalSettings.language}
                onChange={(e) => {
                  setPersonalSettings({ ...personalSettings, language: e.target.value });
                  // Clear error when user changes
                  if (errors.language) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.language;
                      return newErrors;
                    });
                  }
                }}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
              {errors.language && <div className="form-error">{errors.language}</div>}
            </div>
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={personalSettings.notifications_enabled}
                  onChange={(e) => setPersonalSettings({ ...personalSettings, notifications_enabled: e.target.checked })}
                />
                Enable Notifications
              </label>
            </div>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={Object.keys(errors).length > 0}
            >
              Save Personal Settings
            </button>
          </form>
        )}

        {activeTab === 'notifications' && (
          <form onSubmit={handleNotificationPrefsSubmit}>
            <h3 style={{ marginBottom: '20px', color: 'var(--text-color)' }}>Email Notifications</h3>
            <p style={{ color: 'var(--text-light)', marginBottom: '24px', fontSize: '0.95rem' }}>
              Choose which email notifications you want to receive
            </p>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.email_task_assigned}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, email_task_assigned: e.target.checked })}
                />
                <span>
                  <strong>Task Assigned</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    When a task is assigned to you
                  </span>
                </span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.email_task_updated}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, email_task_updated: e.target.checked })}
                />
                <span>
                  <strong>Task Updated</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    When a task you're involved in is updated
                  </span>
                </span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.email_task_commented}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, email_task_commented: e.target.checked })}
                />
                <span>
                  <strong>New Comment</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    When someone comments on your task
                  </span>
                </span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.email_task_due_soon}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, email_task_due_soon: e.target.checked })}
                />
                <span>
                  <strong>Task Due Soon</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    Reminder when a task is due within 24 hours
                  </span>
                </span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.email_task_overdue}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, email_task_overdue: e.target.checked })}
                />
                <span>
                  <strong>Task Overdue</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    Alert when a task becomes overdue
                  </span>
                </span>
              </label>
            </div>
            
            <hr style={{ margin: '32px 0', border: 'none', borderTop: '1px solid var(--border-color)' }} />
            
            <h3 style={{ marginBottom: '20px', color: 'var(--text-color)' }}>In-App Notifications</h3>
            <p style={{ color: 'var(--text-light)', marginBottom: '24px', fontSize: '0.95rem' }}>
              Choose which in-app notifications you want to receive
            </p>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.inapp_task_assigned}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, inapp_task_assigned: e.target.checked })}
                />
                <span><strong>Task Assigned</strong></span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.inapp_task_updated}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, inapp_task_updated: e.target.checked })}
                />
                <span><strong>Task Updated</strong></span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.inapp_task_commented}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, inapp_task_commented: e.target.checked })}
                />
                <span><strong>New Comment</strong></span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.inapp_task_due_soon}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, inapp_task_due_soon: e.target.checked })}
                />
                <span><strong>Task Due Soon</strong></span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.inapp_task_overdue}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, inapp_task_overdue: e.target.checked })}
                />
                <span><strong>Task Overdue</strong></span>
              </label>
            </div>
            
            <hr style={{ margin: '32px 0', border: 'none', borderTop: '1px solid var(--border-color)' }} />
            
            <h3 style={{ marginBottom: '20px', color: 'var(--text-color)' }}>Digest Settings</h3>
            <p style={{ color: 'var(--text-light)', marginBottom: '24px', fontSize: '0.95rem' }}>
              Receive a summary of notifications instead of individual emails
            </p>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.daily_digest}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, daily_digest: e.target.checked })}
                />
                <span>
                  <strong>Daily Digest</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    Receive a daily summary at 9:00 AM
                  </span>
                </span>
              </label>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notificationPrefs.weekly_digest}
                  onChange={(e) => setNotificationPrefs({ ...notificationPrefs, weekly_digest: e.target.checked })}
                />
                <span>
                  <strong>Weekly Digest</strong>
                  <span style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-light)' }}>
                    Receive a weekly summary every Monday at 9:00 AM
                  </span>
                </span>
              </label>
            </div>
            
            <button type="submit" className="btn btn-primary">
              Save Notification Preferences
            </button>
          </form>
        )}

        {activeTab === 'system' && isAdmin() && (
          <form onSubmit={handleSystemSubmit}>
            <div className="form-group">
              <label className="form-label">Site Title</label>
              <input
                type="text"
                className={`form-input ${errors.site_title ? 'has-error' : ''}`}
                value={systemSettings.site_title}
                maxLength={100}
                onChange={(e) => {
                  setSystemSettings({ ...systemSettings, site_title: e.target.value });
                  // Clear error when user changes
                  if (errors.site_title) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.site_title;
                      return newErrors;
                    });
                  }
                }}
                placeholder="Enter site title (2-100 characters)"
              />
              {errors.site_title && <div className="form-error">{errors.site_title}</div>}
              <div className="character-count" style={{ 
                fontSize: '0.875rem', 
                color: systemSettings.site_title.length > 90 ? '#f59e0b' : '#6b7280',
                marginTop: '4px'
              }}>
                {systemSettings.site_title.length} / 100 characters
                {systemSettings.site_title.length > 90 && <span style={{ marginLeft: '4px' }}>(approaching limit)</span>}
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Default Role for New Users</label>
              <select
                className={`form-select ${errors.default_role ? 'has-error' : ''}`}
                value={systemSettings.default_role}
                onChange={(e) => {
                  setSystemSettings({ ...systemSettings, default_role: e.target.value });
                  // Clear error when user changes
                  if (errors.default_role) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.default_role;
                      return newErrors;
                    });
                  }
                }}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
              {errors.default_role && <div className="form-error">{errors.default_role}</div>}
            </div>
            <div className="form-group">
              <label className="form-label">Default Language</label>
              <select
                className={`form-select ${errors.default_language ? 'has-error' : ''}`}
                value={systemSettings.default_language}
                onChange={(e) => {
                  setSystemSettings({ ...systemSettings, default_language: e.target.value });
                  // Clear error when user changes
                  if (errors.default_language) {
                    setErrors(prev => {
                      const newErrors = { ...prev };
                      delete newErrors.default_language;
                      return newErrors;
                    });
                  }
                }}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
              {errors.default_language && <div className="form-error">{errors.default_language}</div>}
            </div>
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={systemSettings.email_notifications_enabled}
                  onChange={(e) => setSystemSettings({ ...systemSettings, email_notifications_enabled: e.target.checked })}
                />
                Enable Email Notifications
              </label>
            </div>
            
            {/* Email Configuration Status */}
            <div className="form-group" style={{ 
              padding: '16px', 
              backgroundColor: systemSettings.email_configured ? '#f0fdf4' : '#fef2f2',
              border: `1px solid ${systemSettings.email_configured ? '#86efac' : '#fca5a5'}`,
              borderRadius: '8px',
              marginTop: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ 
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  color: systemSettings.email_configured ? '#16a34a' : '#dc2626'
                }}>
                  {systemSettings.email_configured ? '✓' : '✗'} Email Configuration
                </span>
              </div>
              <p style={{ 
                margin: 0, 
                fontSize: '0.9rem',
                color: systemSettings.email_configured ? '#166534' : '#991b1b'
              }}>
                {systemSettings.email_configured 
                  ? 'Email is properly configured and ready to send verification codes and notifications.'
                  : 'Email is not configured. Please set SMTP username and password in the fields below to enable email functionality.'}
              </p>
              {systemSettings.smtp_server && (
                <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: '#6b7280' }}>
                  SMTP Server: {systemSettings.smtp_server}:{systemSettings.smtp_port || 587}
                </p>
              )}
            </div>
            
            {/* SMTP Configuration Fields */}
            <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--border-color)' }}>
              <h3 style={{ marginBottom: '16px', color: 'var(--text-color)' }}>SMTP Email Configuration</h3>
              
              <div className="form-group">
                <label className="form-label">SMTP Server</label>
                <input
                  type="text"
                  className="form-input"
                  value={systemSettings.smtp_server || 'smtp.gmail.com'}
                  onChange={(e) => setSystemSettings({ ...systemSettings, smtp_server: e.target.value })}
                  placeholder="smtp.gmail.com"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">SMTP Port</label>
                <input
                  type="number"
                  className="form-input"
                  value={systemSettings.smtp_port || 587}
                  onChange={(e) => setSystemSettings({ ...systemSettings, smtp_port: parseInt(e.target.value) || 587 })}
                  placeholder="587"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">SMTP Username (Email)</label>
                <input
                  type="email"
                  className="form-input"
                  value={systemSettings.smtp_username || ''}
                  onChange={(e) => setSystemSettings({ ...systemSettings, smtp_username: e.target.value })}
                  placeholder="your-email@gmail.com"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">SMTP Password (App Password)</label>
                <input
                  type="password"
                  className="form-input"
                  value={systemSettings.smtp_password || ''}
                  onChange={(e) => setSystemSettings({ ...systemSettings, smtp_password: e.target.value })}
                  placeholder="Enter Gmail app password"
                />
                <small style={{ color: '#6b7280', fontSize: '0.85rem', marginTop: '4px', display: 'block' }}>
                  For Gmail: Use an App Password, not your regular password. Generate at{' '}
                  <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6' }}>
                    myaccount.google.com/apppasswords
                  </a>
                </small>
              </div>
              
              <div className="form-group">
                <label className="form-label">From Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={systemSettings.smtp_from_email || ''}
                  onChange={(e) => setSystemSettings({ ...systemSettings, smtp_from_email: e.target.value })}
                  placeholder="noreply@workhub.com"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">From Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={systemSettings.smtp_from_name || ''}
                  onChange={(e) => setSystemSettings({ ...systemSettings, smtp_from_name: e.target.value })}
                  placeholder="WorkHub Task Management"
                />
              </div>
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={Object.keys(errors).length > 0}
              style={{ marginTop: '24px' }}
            >
              Save System Settings
            </button>
          </form>
        )}
      </div>
      
      {/* Inline styles for validation feedback */}
      <style jsx>{`
        .form-error {
          color: #dc2626;
          font-size: 0.875rem;
          margin-top: 4px;
          display: block;
          animation: slideIn 0.2s ease-out;
        }
        
        .form-input.has-error,
        .form-select.has-error {
          border-color: #dc2626;
          background-color: #fef2f2;
        }
        
        .form-input.has-error:focus,
        .form-select.has-error:focus {
          outline: none;
          border-color: #dc2626;
          box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
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
      `}</style>
    </div>
  );
};

export default Settings;