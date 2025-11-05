import React, { useState, useEffect } from 'react';
import { usersAPI } from '../services/api';
import { FiPlus, FiEdit2, FiTrash2, FiX, FiEye, FiEyeOff } from 'react-icons/fi';
import { PasswordStrength } from '../components/PasswordStrength';
import PendingUsers from '../components/PendingUsers';
import { useModal } from '../hooks/useModal';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/Modal';

// Validators (aligned with backend relaxed rules)
const NAME_REGEX = /^[A-Za-z\s\-']{2,50}$/;
const EMAIL_REGEX = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;

function validateName(name) {
  if (!name || typeof name !== 'string') return 'Name is required.';
  const v = name.trim();
  if (!NAME_REGEX.test(v)) return 'Name must be 2–50 characters and cannot contain numbers or symbols.';
  return null;
}
function validateEmail(email) {
  if (!email || typeof email !== 'string') return 'Email is required.';
  const v = email.trim();
  if (!EMAIL_REGEX.test(v)) return 'Email format is invalid.';
  return null;
}
function validatePassword(password, { required }) {
  if (!password || typeof password !== 'string') return required ? 'Password is required.' : null;
  
  // P0: Enhanced password policy - 10 chars minimum, 3 of 4 character classes
  if (password.length < 10) return 'Password must be at least 10 characters.';
  if (password.length > 128) return 'Password must be less than 128 characters.';
  
  // Check for at least 3 of 4 character classes
  let charClasses = 0;
  if (/[A-Z]/.test(password)) charClasses++;
  if (/[a-z]/.test(password)) charClasses++;
  if (/\d/.test(password)) charClasses++;
  if (/[^A-Za-z0-9]/.test(password)) charClasses++;
  
  if (charClasses < 3) return 'Password must include at least 3 of: uppercase, lowercase, digit, special character.';
  
  // Check for common weak passwords
  const commonPasswords = ['password123', 'qwerty123', 'abc123456', 'welcome123', 'admin123'];
  if (commonPasswords.includes(password.toLowerCase())) return 'Password is too common.';
  
  return null;
}
function validateConfirmPassword(password, confirm, { required }) {
  if (required && (confirm === undefined || confirm === null || confirm === '')) {
    return 'Confirm your password.';
  }
  if (confirm && password !== confirm) return 'Passwords do not match.';
  return null;
}

const Users = () => {
  const { user: currentUser } = useAuth();
  const { modalState, showAlert, showConfirm, showError, showSuccess, closeModal: closeGlobalModal } = useModal();
  const [users, setUsers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirm: '',
    role: 'viewer',
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [pwVisible, setPwVisible] = useState(false);
  const [cpwVisible, setCpwVisible] = useState(false);
  const [viewingPassword, setViewingPassword] = useState(null);
  const [passwordDetails, setPasswordDetails] = useState(null);

  const fetchUsers = async () => {
    try {
      const { data } = await usersAPI.getAll();
      setUsers(data || []);
    } catch (err) {
      showError(err?.response?.data?.error || 'Failed to load users', 'Error Loading Users');
    }
  };
  useEffect(() => { fetchUsers(); }, []);

  const openCreate = () => {
    setSelectedUser(null);
    setFormData({ name: '', email: '', password: '', confirm: '', role: 'viewer' });
    setErrors({});
    setPwVisible(false);
    setCpwVisible(false);
    setShowModal(true);
  };
  const openEdit = (user) => {
    setSelectedUser(user);
    setFormData({
      name: user.name || '',
      email: user.email || '',
      password: '',
      confirm: '',
      role: user.role || 'viewer',
    });
    setErrors({});
    setPwVisible(false);
    setCpwVisible(false);
    setShowModal(true);
  };
  const closeModal = () => {
    setShowModal(false);
    setSelectedUser(null);
    setFormData({ name: '', email: '', password: '', confirm: '', role: 'viewer' });
    setErrors({});
  };
  const onChange = (key, value) => setFormData((s) => ({ ...s, [key]: value }));

  const runValidation = () => {
    const e = {};
    const isCreate = !selectedUser;

    const eName = validateName(formData.name);
    if (eName) e.name = eName;

    const eEmail = validateEmail(formData.email);
    if (eEmail) e.email = eEmail;

    const ePw = validatePassword(formData.password, { required: isCreate });
    if (ePw) e.password = ePw;

    const eC = validateConfirmPassword(formData.password, formData.confirm, { required: isCreate });
    if (eC) e.confirm = eC;

    const role = (formData.role || '').toLowerCase();
    const validRoles = ['super_admin', 'admin', 'manager', 'team_lead', 'developer', 'viewer'];
    if (!validRoles.includes(role)) e.role = `Role must be one of: ${validRoles.join(', ')}.`;

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!runValidation()) return;

    setSubmitting(true);
    try {
      if (selectedUser) {
        const payload = {
          name: formData.name.trim(),
          email: formData.email.trim(),
          role: (formData.role || 'viewer').toLowerCase(),
        };
        if (formData.password) {
          payload.password = formData.password;
          if (formData.confirm) payload.confirm = formData.confirm;
        }
        await usersAPI.update(selectedUser.id, payload);
      } else {
        const payload = {
          name: formData.name.trim(),
          email: formData.email.trim(),
          password: formData.password,
          confirm: formData.confirm,
          role: (formData.role || 'viewer').toLowerCase(),
        };
        await usersAPI.create(payload);
      }
      setSubmitting(false);
      closeModal();
      fetchUsers();
    } catch (error) {
      setSubmitting(false);
      showError(error?.response?.data?.error || error?.message || 'Failed to save user', 'Error Saving User');
    }
  };

  const handleDelete = async (user) => {
    const confirmed = await showConfirm(
      `Delete user "${user.name}"? This action cannot be undone.`,
      'Delete User'
    );
    
    if (!confirmed) return;
    
    try {
      await usersAPI.delete(user.id);
      fetchUsers();
      showSuccess('User deleted successfully');
    } catch (error) {
      showError(error?.response?.data?.error || 'Failed to delete user', 'Error Deleting User');
    }
  };

  const handleViewPassword = async (user) => {
    try {
      // Use the details endpoint for super admin to get password hash
      const response = await fetch(`/api/users/${user.id}/details`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch user details');
      }
      
      const data = await response.json();
      setPasswordDetails(data);
      setViewingPassword(user.id);
    } catch (error) {
      showError(error?.message || 'Failed to load user details', 'Error');
    }
  };

  const RoleBadge = ({ role }) => {
    const r = (role || '').toLowerCase();
    const roleClass = r === 'super_admin' ? 'super-admin' :
                     r === 'admin' ? 'admin' :
                     r === 'manager' ? 'manager' :
                     r === 'team_lead' ? 'team-lead' :
                     r === 'developer' ? 'developer' : 'viewer';
    const displayName = r === 'super_admin' ? 'Super Admin' :
                       r === 'admin' ? 'Admin' :
                       r === 'manager' ? 'Manager' :
                       r === 'team_lead' ? 'Team Lead' :
                       r === 'developer' ? 'Developer' : 'Viewer';
    return (
      <span className={`role-badge ${roleClass}`}>
        {displayName}
      </span>
    );
  };

  return (
    <div>
      <div className="page-header">
        <h1>Users</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          <FiPlus style={{ marginRight: 6 }} />
          Add User
        </button>
      </div>

      {/* Pending Users Section */}
      <PendingUsers />

      {/* List */}
      <div className="card">
        <div className="card-body">
          {users.length === 0 ? (
            <p>No users yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: '35%' }}>Name</th>
                  <th style={{ width: '35%' }}>Email</th>
                  <th style={{ width: '15%' }}>Role</th>
                  <th style={{ width: '15%' }}></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td><RoleBadge role={u.role} /></td>
                    <td>
                      <div className="actions">
                        {currentUser?.role === 'super_admin' && (
                          <button
                            className="btn btn-sm btn-icon"
                            onClick={() => handleViewPassword(u)}
                            title="View Password Details"
                            aria-label="View Password Details"
                          >
                            <FiEye />
                          </button>
                        )}
                        {(currentUser?.role === 'admin' || currentUser?.role === 'super_admin') && (
                          <button
                            className="btn btn-sm btn-icon"
                            onClick={() => openEdit(u)}
                            title="Edit User"
                            aria-label="Edit User"
                          >
                            <FiEdit2 />
                          </button>
                        )}
                        {(currentUser?.role === 'admin' || currentUser?.role === 'super_admin') && (
                          <button
                            className="btn btn-sm btn-icon btn-danger"
                            onClick={() => handleDelete(u)}
                            title="Delete User"
                            aria-label="Delete User"
                          >
                            <FiTrash2 />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>{selectedUser ? 'Edit User' : 'Add User'}</h2>
              <button className="icon-button" onClick={closeModal} aria-label="Close">
                <FiX />
              </button>
            </div>

            {/* Make only the body scroll; footer stays visible */}
            <form onSubmit={handleSubmit} className="modal-content">
              <div className="modal-body">
                {/* Name */}
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input
                    className={`form-input ${errors.name ? 'has-error' : ''}`}
                    value={formData.name}
                    onChange={(e) => onChange('name', e.target.value)}
                    placeholder="Full name (no numbers)"
                    autoFocus
                  />
                  {errors.name && <div className="form-error">{errors.name}</div>}
                </div>

                {/* Email */}
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className={`form-input ${errors.email ? 'has-error' : ''}`}
                    value={formData.email}
                    onChange={(e) => onChange('email', e.target.value)}
                    placeholder="name@example.com"
                  />
                  {errors.email && <div className="form-error">{errors.email}</div>}
                </div>

                {/* Password + Show/Hide */}
                <div className="form-group">
                  <label className="form-label">
                    Password {selectedUser ? <span className="muted">(leave blank to keep)</span> : null}
                  </label>
                  <div className="input-with-icon">
                    <input
                      className={`form-input ${errors.password ? 'has-error' : ''}`}
                      type={pwVisible ? 'text' : 'password'}
                      value={formData.password}
                      onChange={(e) => onChange('password', e.target.value)}
                      placeholder="At least 10 characters, 3 of 4: upper/lower/digit/special"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="icon-button eye"
                      onClick={() => setPwVisible((s) => !s)}
                      title={pwVisible ? 'Hide password' : 'Show password'}
                      aria-label={pwVisible ? 'Hide password' : 'Show password'}
                    >
                      {pwVisible ? <FiEyeOff /> : <FiEye />}
                    </button>
                  </div>
                  {errors.password && <div className="form-error">{errors.password}</div>}
                  {formData.password && <PasswordStrength password={formData.password} />}
                </div>

                {/* Confirm + Show/Hide */}
                <div className="form-group">
                  <label className="form-label">
                    Confirm Password {selectedUser ? <span className="muted">(optional)</span> : null}
                  </label>
                  <div className="input-with-icon">
                    <input
                      className={`form-input ${errors.confirm ? 'has-error' : ''}`}
                      type={cpwVisible ? 'text' : 'password'}
                      value={formData.confirm}
                      onChange={(e) => onChange('confirm', e.target.value)}
                      placeholder="Re-enter password"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="icon-button eye"
                      onClick={() => setCpwVisible((s) => !s)}
                      title={cpwVisible ? 'Hide password' : 'Show password'}
                      aria-label={cpwVisible ? 'Hide password' : 'Show password'}
                    >
                      {cpwVisible ? <FiEyeOff /> : <FiEye />}
                    </button>
                  </div>
                  {errors.confirm && <div className="form-error">{errors.confirm}</div>}
                </div>

                {/* Role */}
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <select
                    className={`form-input ${errors.role ? 'has-error' : ''}`}
                    value={formData.role}
                    onChange={(e) => onChange('role', e.target.value)}
                  >
                    <option value="super_admin">Super Admin</option>
                    <option value="admin">Admin</option>
                    <option value="manager">Manager</option>
                    <option value="team_lead">Team Lead</option>
                    <option value="developer">Developer</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  {errors.role && <div className="form-error">{errors.role}</div>}
                </div>
              </div>

              {/* Footer stays pinned and visible */}
              <div className="modal-footer">
                <button type="button" className="btn" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? (selectedUser ? 'Updating...' : 'Creating...') : selectedUser ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Component-scoped styles */}
      <style>{`
        .page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom: 16px; }
        .card { background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
        .card-body { padding: 16px; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 10px; border-bottom: 1px solid #eee; vertical-align: middle; }
        .text-right { text-align: right; }
        .actions { display:flex; justify-content:flex-end; gap: 8px; }
        .btn-icon { width: 34px; height: 34px; display:flex; align-items:center; justify-content:center; }
        .btn { padding: 8px 12px; border-radius: 8px; border: 1px solid #ddd; background: #f7f7f7; }
        .btn:hover { background: #efefef; }
        .btn-primary { background: #68939d; border-color: #68939d; color: #fff; }
        .btn-primary:hover { background: #1d4ed8; }
        .btn-danger { background: #ef4444; border-color: #ef4444; color:#fff; }
        .btn-sm { padding: 6px 8px; border-radius: 6px; }

        /* Role badges */
        .role-badge { display:inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
        .role-badge.super-admin { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .role-badge.admin { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
        .role-badge.manager { background: #ddd6fe; color: #6b21a8; border: 1px solid #c4b5fd; }
        .role-badge.team-lead { background: #e0eef1; color: #4f7e86; border: 1px solid #b8d1d6; }
        .role-badge.developer { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .role-badge.viewer { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; }

        /* Modal overlay */
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display:flex; align-items:center; justify-content:center; z-index: 50; padding: 16px; }
        .modal { width: 100%; max-width: 620px; background: #fff; border-radius: 14px; box-shadow: 0 12px 40px rgba(0,0,0,.2); display: flex; flex-direction: column; max-height: 90vh; }
        .modal-header { display:flex; align-items:center; justify-content:space-between; padding: 16px 18px; border-bottom: 1px solid #eee; }
        .modal-content { display:flex; flex-direction:column; min-height: 0; }
        .modal-body { padding: 16px 18px; overflow: auto; min-height: 0; }
        .modal-footer { display:flex; justify-content:flex-end; gap: 10px; padding: 12px 18px; border-top: 1px solid #eee; background: #fafafa; }

        .form-group { margin-bottom: 14px; }
        .form-label { display:block; font-weight: 600; margin-bottom: 6px; color: #0f172a; }
        .form-input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 10px; background: #fff; }
        .form-input.has-error { border-color: #ef4444; }
        .form-error { color: #dc2626; font-size: 0.875rem; margin-top: 6px; }
        .muted { color:#6b7280; font-weight: 400; margin-left: 4px; }

        .icon-button { border: none; background: transparent; padding: 6px; border-radius: 6px; cursor: pointer; }
        .icon-button:hover { background: #f2f2f2; }
        .input-with-icon { position: relative; display: flex; align-items: center; }
        .input-with-icon input { width: 100%; padding-right: 40px; }
        .input-with-icon .icon-button.eye { position: absolute; right: 6px; }
        
        @media (max-height: 700px) {
          .modal { max-height: 94vh; }
        }
      `}</style>

      {/* Password Details Modal for Super Admin */}
      {viewingPassword && passwordDetails && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>User Password Details - {passwordDetails.name}</h2>
              <button className="icon-button" onClick={() => { setViewingPassword(null); setPasswordDetails(null); }} aria-label="Close">
                <FiX />
              </button>
            </div>
            <div className="modal-content">
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input type="text" className="form-input" value={passwordDetails.email || ''} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Password Hash (BCrypt)</label>
                  <textarea
                    className="form-input"
                    value={passwordDetails.password_hash || 'Not available'}
                    readOnly
                    rows="3"
                    style={{ fontFamily: 'monospace', fontSize: '12px' }}
                  />
                </div>
                {passwordDetails.reset_token && (
                  <div className="form-group">
                    <label className="form-label">Reset Token</label>
                    <input type="text" className="form-input" value={passwordDetails.reset_token || ''} readOnly style={{ fontFamily: 'monospace', fontSize: '12px' }} />
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Force Password Change</label>
                  <input type="text" className="form-input" value={passwordDetails.force_password_change ? 'Yes' : 'No'} readOnly />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-primary" onClick={() => { setViewingPassword(null); setPasswordDetails(null); }}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Global Modal Component */}
      <Modal
        isOpen={modalState.isOpen}
        onClose={closeGlobalModal}
        onConfirm={modalState.onConfirm}
        title={modalState.title}
        message={modalState.message}
        type={modalState.type}
        confirmText={modalState.confirmText}
        cancelText={modalState.cancelText}
        showCancel={modalState.showCancel}
      >
        {modalState.children}
      </Modal>
    </div>
  );
};

export default Users;
