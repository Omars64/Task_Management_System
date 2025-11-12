import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsAPI } from '../services/api';
import { FiCheckCircle, FiTrash2 } from 'react-icons/fi';
import { useModal } from '../hooks/useModal';
import { useToast } from '../context/ToastContext';
import Modal from '../components/Modal';
import { formatLocalDateTime } from '../utils/dateTime';

const Notifications = () => {
  const { modalState, showConfirm, showSuccess, closeModal } = useModal();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState(null);

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

  const handleNotificationClick = async (notification) => {
    // Don't resolve if already resolving or if notification has no related resource
    if (resolvingId || (!notification.related_task_id && !notification.related_conversation_id && !notification.related_group_id)) {
      return;
    }

    setResolvingId(notification.id);
    try {
      const response = await notificationsAPI.resolve(notification.id);
      const { redirect_url, error } = response.data;

      if (error || !redirect_url) {
        addToast(error || 'Unable to navigate to this notification', { type: 'error' });
        // Refresh notifications to update read status
        fetchNotifications();
        window.dispatchEvent(new Event('notifications:refresh-count'));
      } else {
        // Navigate to the resolved URL
        navigate(redirect_url);
        // Refresh notifications to update read status
        fetchNotifications();
        window.dispatchEvent(new Event('notifications:refresh-count'));
      }
    } catch (error) {
      console.error('Failed to resolve notification:', error);
      const errorMsg = error.response?.data?.error || 'Failed to navigate to notification';
      addToast(errorMsg, { type: 'error' });
    } finally {
      setResolvingId(null);
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
            {notifications.map(notif => {
              const isClickable = notif.related_task_id || notif.related_conversation_id || notif.related_group_id;
              const isResolving = resolvingId === notif.id;
              
              return (
                <div
                  key={notif.id}
                  onClick={() => isClickable && handleNotificationClick(notif)}
                  style={{
                    padding: '16px',
                    backgroundColor: notif.is_read ? 'white' : '#f0f9ff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    cursor: isClickable ? 'pointer' : 'default',
                    transition: 'all 0.2s ease',
                    opacity: isResolving ? 0.6 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (isClickable) {
                      e.currentTarget.style.backgroundColor = notif.is_read ? '#f8f9fa' : '#e0f2fe';
                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (isClickable) {
                      e.currentTarget.style.backgroundColor = notif.is_read ? 'white' : '#f0f9ff';
                      e.currentTarget.style.boxShadow = 'none';
                    }
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>
                      {notif.title}
                      {isClickable && (
                        <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: '8px', fontStyle: 'italic' }}>
                          (Click to view)
                        </span>
                      )}
                    </h3>
                    <p style={{ fontSize: '14px', color: 'var(--text-light)', marginBottom: '8px' }}>
                      {notif.message}
                    </p>
                    <span style={{ fontSize: '12px', color: 'var(--text-light)' }}>
                      {formatLocalDateTime(notif.created_at)}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }} onClick={(e) => e.stopPropagation()}>
                    {!notif.is_read && (
                      <button 
                        className="btn btn-sm btn-primary" 
                        onClick={() => handleMarkAsRead(notif.id)}
                        disabled={isResolving}
                      >
                        Mark Read
                      </button>
                    )}
                    <button 
                      className="icon-btn" 
                      onClick={() => handleDelete(notif.id)}
                      disabled={isResolving}
                    >
                      <FiTrash2 />
                    </button>
                  </div>
                </div>
              );
            })}
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