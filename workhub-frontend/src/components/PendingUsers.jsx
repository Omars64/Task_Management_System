import React, { useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import { FiCheck, FiX, FiClock, FiMail, FiUser } from 'react-icons/fi';
import { useModal } from '../hooks/useModal';
import { useToast } from '../context/ToastContext';
import Modal from './Modal';

const PendingUsers = () => {
  const { modalState, showAlert, showConfirm, showError, showSuccess, closeModal } = useModal();
  const { addToast } = useToast();
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('pending'); // 'pending' | 'rejected'
  const [rejectedUsers, setRejectedUsers] = useState([]);
  const [isOpen, setIsOpen] = useState(false); // collapsible state
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'pending') {
      fetchPendingUsers();
    } else {
      fetchRejectedUsers();
    }
  }, [activeTab]);

  const fetchPendingUsers = async () => {
    setLoading(true);
    try {
      const response = await authAPI.getPendingUsers();
      setPendingUsers(response.data.pending_users || []);
    } catch (error) {
      console.error('Failed to fetch pending users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRejectedUsers = async () => {
    setLoading(true);
    try {
      const response = await authAPI.getRejectedUsers();
      setRejectedUsers(response.data.rejected_users || []);
    } catch (error) {
      console.error('Failed to fetch rejected users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (user) => {
    const confirmed = await showConfirm(
      `Approve signup for ${user.name} (${user.email})? They will be able to log in after approval.`,
      'Approve User Signup'
    );
    
    if (!confirmed) {
      return;
    }

    setActionLoading(true);
    try {
      await authAPI.approveUser(user.id);
      showSuccess(`${user.name} has been approved and notified via email!`, 'User Approved');
      fetchPendingUsers(); // Refresh list
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to approve user', 'Error Approving User');
    } finally {
      setActionLoading(false);
    }
  };

  const openRejectModal = (user) => {
    setSelectedUser(user);
    setRejectionReason('');
    setShowRejectModal(true);
  };

  const closeRejectModal = () => {
    setShowRejectModal(false);
    setSelectedUser(null);
    setRejectionReason('');
  };

  const handleReject = async () => {
    if (!selectedUser) return;

    // Store user info and reason before closing modal
    const userId = selectedUser.id;
    const userName = selectedUser.name;
    const reason = rejectionReason;
    
    // Close modal immediately for better UX
    closeRejectModal();
    
    // Show toast immediately
    addToast(`Rejecting ${userName}...`, { type: 'info', timeout: 2000 });

    try {
      await authAPI.rejectUser(userId, reason);
      addToast(`${userName}'s signup has been rejected and user has been notified.`, { type: 'success' });
      fetchPendingUsers(); // Refresh list
    } catch (error) {
      addToast(error.response?.data?.error || 'Failed to reject user', { type: 'error' });
      // Reopen modal if error occurred
      const user = pendingUsers.find(u => u.id === userId);
      if (user) {
        setSelectedUser(user);
        setRejectionReason(reason);
        setShowRejectModal(true);
      }
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Always render the container; show/hide list body with isOpen

  return (
    <div className="pending-users-container">
      <div style={{ display:'flex', gap:12, marginBottom:12, alignItems:'center', justifyContent:'space-between' }}>
        <div style={{ display:'flex', gap:12 }}>
          <button
            className={`btn ${activeTab==='pending' ? 'btn-primary' : ''}`}
            onClick={() => { setActiveTab('pending'); setIsOpen(true); }}
          >Pending</button>
          <button
            className={`btn ${activeTab==='rejected' ? 'btn-primary' : ''}`}
            onClick={() => { setActiveTab('rejected'); setIsOpen(true); }}
          >Rejected</button>
        </div>
        <button className="btn" onClick={() => setIsOpen((v) => !v)}>
          {isOpen ? 'Hide' : 'Show'}
        </button>
      </div>
      <div className="pending-users-header">
        <h3>
          <FiClock style={{ marginRight: 8 }} />
          {activeTab === 'pending' ? `Pending User Signups (${pendingUsers.length})` : `Rejected Signups (${rejectedUsers.length})`}
        </h3>
        <p>{activeTab === 'pending' ? 'Review and approve or reject new user registrations' : 'Review previously rejected signups'}</p>
      </div>

      {isOpen && (
        <>
          {loading ? (
            <div className="loading">Loading users...</div>
          ) : (
            <>
              {(() => {
                const list = activeTab === 'pending' ? pendingUsers : rejectedUsers;
                if (!list || list.length === 0) {
                  return (
                    <div className="empty-state">
                      <FiClock size={48} color="#9ca3af" />
                      <h3>{activeTab === 'pending' ? 'No Pending Signups' : 'No Rejected Signups'}</h3>
                      <p>{activeTab === 'pending' ? 'There are no user signups waiting for approval.' : 'There are no rejected signups.'}</p>
                    </div>
                  );
                }
                return (
                  <div className="pending-users-list">
                    {list.map((user) => (
                      <div key={user.id} className="pending-user-card">
                        <div className="pending-user-info">
                          <div className="pending-user-avatar">
                            <FiUser size={24} />
                          </div>
                          <div className="pending-user-details">
                            <h4>{user.name}</h4>
                            <p className="user-email">
                              <FiMail size={14} />
                              {user.email}
                            </p>
                            <p className="user-meta">
                              Signed up: {formatDate(user.created_at)}
                            </p>
                            <div className="user-status">
                              {user.email_verified ? (
                                <span className="badge badge-success">✓ Email Verified</span>
                              ) : (
                                <span className="badge badge-warning">⚠ Email Not Verified</span>
                              )}
                            </div>
                          </div>
                        </div>
                        {activeTab === 'pending' ? (
                          <div className="pending-user-actions">
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handleApprove(user)}
                              disabled={actionLoading}
                              title="Approve User"
                            >
                              <FiCheck /> Approve
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => openRejectModal(user)}
                              disabled={actionLoading}
                              title="Reject User"
                            >
                              <FiX /> Reject
                            </button>
                          </div>
                        ) : (
                          <div className="pending-user-actions">
                            <span className="badge badge-warning">Rejected</span>
                            {user.rejection_reason ? (
                              <span className="badge" style={{ background:'#fee2e2', color:'#991b1b' }}>Reason: {user.rejection_reason}</span>
                            ) : null}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                );
              })()}
            </>
          )}
        </>
      )}

      {/* Reject Modal */}
      {showRejectModal && selectedUser && (
        <div className="modal-overlay" onClick={closeRejectModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Reject Signup</h3>
              <button className="modal-close" onClick={closeRejectModal}>
                <FiX />
              </button>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to reject the signup for <strong>{selectedUser.name}</strong>?
              </p>
              <div className="form-group">
                <label className="form-label">
                  Reason (Optional - will be sent to user)
                </label>
                <textarea
                  className="form-input"
                  rows={4}
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="e.g., Email domain not allowed, duplicate account, etc."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={closeRejectModal}
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={handleReject}
                disabled={actionLoading}
              >
                {actionLoading ? 'Rejecting...' : 'Reject Signup'}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .pending-users-container {
          margin-bottom: 32px;
        }

        .pending-users-header {
          margin-bottom: 20px;
        }

        .pending-users-header h3 {
          display: flex;
          align-items: center;
          color: #111827;
          margin-bottom: 8px;
        }

        .pending-users-header p {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .pending-users-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .pending-user-card {
          background: #fffbeb;
          border: 1px solid #fbbf24;
          border-radius: 8px;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
        }

        .pending-user-info {
          display: flex;
          gap: 16px;
          align-items: center;
          flex: 1;
        }

        .pending-user-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: #fef3c7;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #f59e0b;
          flex-shrink: 0;
        }

        .pending-user-details {
          flex: 1;
        }

        .pending-user-details h4 {
          margin: 0 0 4px 0;
          color: #111827;
          font-size: 1rem;
        }

        .user-email {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #6b7280;
          font-size: 0.875rem;
          margin: 4px 0;
        }

        .user-meta {
          color: #9ca3af;
          font-size: 0.75rem;
          margin: 4px 0;
        }

        .user-status {
          margin-top: 8px;
        }

        .badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .badge-success {
          background: #d1fae5;
          color: #065f46;
        }

        .badge-warning {
          background: #fef3c7;
          color: #92400e;
        }

        .pending-user-actions {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }

        .btn-sm {
          padding: 8px 16px;
          font-size: 0.875rem;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .btn-success {
          background-color: #10b981;
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          background-color: #059669;
        }

        .btn-danger {
          background-color: #ef4444;
          color: white;
        }

        .btn-danger:hover:not(:disabled) {
          background-color: #dc2626;
        }

        .empty-state {
          text-align: center;
          padding: 48px 24px;
          color: #6b7280;
        }

        .empty-state h3 {
          margin: 16px 0 8px 0;
          color: #374151;
        }

        .loading {
          text-align: center;
          padding: 24px;
          color: #6b7280;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          width: 90%;
          max-width: 500px;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h3 {
          margin: 0;
          color: #111827;
        }

        .modal-close {
          background: none;
          border: none;
          cursor: pointer;
          padding: 4px;
          color: #6b7280;
        }

        .modal-close:hover {
          color: #111827;
        }

        .modal-body {
          padding: 20px;
        }

        .modal-body p {
          margin-bottom: 16px;
          color: #374151;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid #e5e7eb;
        }

        .btn-secondary {
          background-color: #f3f4f6;
          color: #374151;
        }

        .btn-secondary:hover:not(:disabled) {
          background-color: #e5e7eb;
        }
      `}</style>

      {/* Global Modal Component for success/error messages */}
      <Modal
        isOpen={modalState.isOpen}
        onClose={closeModal}
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

export default PendingUsers;

