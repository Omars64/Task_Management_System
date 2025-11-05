import { useState, useCallback } from 'react';

/**
 * Custom hook for managing modal state
 * Provides alert, confirm, and custom modal functionality
 */
export const useModal = () => {
  const [modalState, setModalState] = useState({
    isOpen: false,
    type: 'info',
    title: '',
    message: '',
    confirmText: 'OK',
    cancelText: 'Cancel',
    showCancel: false,
    onConfirm: null,
    children: null
  });

  // Show alert modal (single OK button)
  const showAlert = useCallback((message, title = '', type = 'info') => {
    return new Promise((resolve) => {
      setModalState({
        isOpen: true,
        type,
        title,
        message,
        confirmText: 'OK',
        cancelText: 'Cancel',
        showCancel: false,
        onConfirm: () => resolve(true),
        children: null
      });
    });
  }, []);

  // Show confirm modal (Cancel and Confirm buttons)
  const showConfirm = useCallback((message, title = 'Confirm', type = 'confirm') => {
    return new Promise((resolve) => {
      setModalState({
        isOpen: true,
        type,
        title,
        message,
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        showCancel: true,
        onConfirm: () => resolve(true),
        onCancel: () => resolve(false),
        children: null
      });
    });
  }, []);

  // Show success modal
  const showSuccess = useCallback((message, title = 'Success') => {
    return showAlert(message, title, 'success');
  }, [showAlert]);

  // Show error modal
  const showError = useCallback((message, title = 'Error') => {
    return showAlert(message, title, 'error');
  }, [showAlert]);

  // Show warning modal
  const showWarning = useCallback((message, title = 'Warning') => {
    return showAlert(message, title, 'warning');
  }, [showAlert]);

  // Show custom modal with children
  const showCustom = useCallback((config) => {
    return new Promise((resolve) => {
      setModalState({
        isOpen: true,
        type: config.type || 'info',
        title: config.title || '',
        message: config.message || '',
        confirmText: config.confirmText || 'OK',
        cancelText: config.cancelText || 'Cancel',
        showCancel: config.showCancel || false,
        onConfirm: () => resolve(true),
        children: config.children || null
      });
    });
  }, []);

  // Close modal
  const closeModal = useCallback(() => {
    // Call onCancel if it exists (for confirm dialogs)
    if (modalState.onCancel) {
      modalState.onCancel();
    }
    setModalState(prev => ({ ...prev, isOpen: false }));
  }, [modalState]);

  return {
    modalState,
    showAlert,
    showConfirm,
    showSuccess,
    showError,
    showWarning,
    showCustom,
    closeModal
  };
};

