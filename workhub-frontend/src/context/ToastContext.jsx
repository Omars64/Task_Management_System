import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

const ToastContext = createContext({ addToast: () => {} });

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, { type = 'info', timeout = 2800 } = {}) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, type }]);
    if (timeout) {
      setTimeout(() => removeToast(id), timeout);
    }
    return id;
  }, [removeToast]);

  const value = useMemo(() => ({ addToast, toasts, removeToast }), [addToast, toasts, removeToast]);

  return (
    <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}


