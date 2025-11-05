import React, { useEffect } from 'react';
import './Modal.css';

/**
 * Reusable Modal Component
 * Supports alert, confirm, and custom content modes
 */
const Modal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  type = 'info', // 'success', 'error', 'warning', 'info', 'confirm'
  confirmText = 'OK',
  cancelText = 'Cancel',
  showCancel = false,
  children
}) => {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden'; // Prevent background scroll
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const getIcon = () => {
    switch (type) {
      case 'success':
        return (
          <div className="modal-icon modal-icon-success">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="modal-icon modal-icon-error">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
          </div>
        );
      case 'warning':
        return (
          <div className="modal-icon modal-icon-warning">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
        );
      case 'confirm':
        return (
          <div className="modal-icon modal-icon-confirm">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
        );
      default: // info
        return (
          <div className="modal-icon modal-icon-info">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
        );
    }
  };

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-content">
          {getIcon()}
          
          {title && <h2 className="modal-title">{title}</h2>}
          
          {message && <p className="modal-message">{message}</p>}
          
          {children && <div className="modal-custom-content">{children}</div>}
        </div>

        <div className="modal-actions">
          {showCancel && (
            <button
              className="modal-btn modal-btn-cancel"
              onClick={onClose}
              type="button"
            >
              {cancelText}
            </button>
          )}
          <button
            className={`modal-btn modal-btn-primary ${type === 'error' ? 'modal-btn-danger' : type === 'warning' ? 'modal-btn-warning' : ''}`}
            onClick={handleConfirm}
            type="button"
            autoFocus
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Modal;

