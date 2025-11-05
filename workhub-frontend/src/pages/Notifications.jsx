import React, { useState, useEffect } from 'react';
import { notificationsAPI } from '../services/api';
import { FiCheckCircle, FiTrash2 } from 'react-icons/fi';
import { useModal } from '../hooks/useModal';
import Modal from '../components/Modal';

const Notifications = () => {
  const { modalState, showConfirm, showSuccess, closeModal } = useModal();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On open, fetch and mark all as read so sidebar badge clears immediately
    fetchNotifications();
    (async () => {
      try {
        await notificationsAPI.markAllAsRead();
        // inform layout to refresh unread badge
        window.dispatchEvent(new Event('notifications:refresh-count'));
        fetchNotifications();
      } catch (e) {}
    })();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await notificationsAPI.getAll();
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await notificationsAPI.markAsRead(id);
      fetchNotifications();
      window.dispatchEvent(new Event('notifications:refresh-count'));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsAPI.markAllAsRead();
      fetchNotifications();
      window.dispatchEvent(new Event('notifications:refresh-count'));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationsAPI.delete(id);
      fetchNotifications();
      window.dispatchEvent(new Event('notifications:refresh-count'));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const handleClearAll = async () => {
    const confirmed = await showConfirm(
      'Are you sure you want to clear all notifications? This action cannot be undone.',
      'Clear All Notifications'
    );
    
    if (confirmed) {
      try {
        await notificationsAPI.clearAll();
        fetchNotifications();
        showSuccess('All notifications cleared successfully');
        window.dispatchEvent(new Event('notifications:refresh-count'));
      } catch (error) {
        console.error('Failed to clear notifications:', error);
      }
    }
  };

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="page-header">
        <h1>Notifications</h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-outline" onClick={handleMarkAllAsRead}>
            <FiCheckCircle /> Mark All as Read
          </button>
          <button className="btn btn-danger" onClick={handleClearAll}>
            <FiTrash2 /> Clear All
          </button>
        </div>
      </div>

      <div className="card">
        {notifications.length === 0 ? (
          <p className="text-center text-light">No notifications</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {notifications.map(notif => (
              <div
                key={notif.id}
                style={{
                  padding: '16px',
                  backgroundColor: notif.is_read ? 'white' : '#f0f9ff',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start'
                }}
              >
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>
                    {notif.title}
                  </h3>
                  <p style={{ fontSize: '14px', color: 'var(--text-light)', marginBottom: '8px' }}>
                    {notif.message}
                  </p>
                  <span style={{ fontSize: '12px', color: 'var(--text-light)' }}>
                    {new Date(notif.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {!notif.is_read && (
                    <button className="btn btn-sm btn-primary" onClick={() => handleMarkAsRead(notif.id)}>
                      Mark Read
                    </button>
                  )}
                  <button className="icon-btn" onClick={() => handleDelete(notif.id)}>
                    <FiTrash2 />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Component */}
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

export default Notifications;