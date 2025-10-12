import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { settingsAPI, usersAPI } from '../services/api';

const Settings = () => {
  const { user, isAdmin, updateUser } = useAuth();
  const { theme, setTheme } = useTheme();
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
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const personalRes = await settingsAPI.getPersonal();
      setPersonalSettings(personalRes.data);
      
      // Sync theme with context
      if (personalRes.data.theme !== theme) {
        setTheme(personalRes.data.theme);
      }
      
      if (isAdmin()) {
        const systemRes = await settingsAPI.getSystem();
        setSystemSettings(systemRes.data);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const handlePersonalSubmit = async (e) => {
    e.preventDefault();
    try {
      await settingsAPI.updatePersonal(personalSettings);
      
      // Update theme in context
      setTheme(personalSettings.theme);
      
      // Update user in context
      const updatedUser = await usersAPI.getById(user.id);
      updateUser(updatedUser.data);
      
      setMessage('Personal settings updated successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      alert('Failed to update personal settings');
    }
  };

  const handleSystemSubmit = async (e) => {
    e.preventDefault();
    try {
      await settingsAPI.updateSystem(systemSettings);
      setMessage('System settings updated successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      alert('Failed to update system settings');
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
                className="form-select"
                value={personalSettings.theme}
                onChange={(e) => setPersonalSettings({ ...personalSettings, theme: e.target.value })}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Language</label>
              <select
                className="form-select"
                value={personalSettings.language}
                onChange={(e) => setPersonalSettings({ ...personalSettings, language: e.target.value })}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
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
            <button type="submit" className="btn btn-primary">Save Personal Settings</button>
          </form>
        )}

        {activeTab === 'system' && isAdmin() && (
          <form onSubmit={handleSystemSubmit}>
            <div className="form-group">
              <label className="form-label">Site Title</label>
              <input
                type="text"
                className="form-input"
                value={systemSettings.site_title}
                onChange={(e) => setSystemSettings({ ...systemSettings, site_title: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Default Role for New Users</label>
              <select
                className="form-select"
                value={systemSettings.default_role}
                onChange={(e) => setSystemSettings({ ...systemSettings, default_role: e.target.value })}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Default Language</label>
              <select
                className="form-select"
                value={systemSettings.default_language}
                onChange={(e) => setSystemSettings({ ...systemSettings, default_language: e.target.value })}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
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
            <button type="submit" className="btn btn-primary">Save System Settings</button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Settings;