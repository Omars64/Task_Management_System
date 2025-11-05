import React from 'react';
import { useToast } from '../context/ToastContext';

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();
  if (!toasts || toasts.length === 0) return null;
  return (
    <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', display: 'grid', gap: 8, zIndex: 2000, alignItems: 'center', justifyItems: 'center' }}>
      {toasts.map((t) => (
        <div
          key={t.id}
          onClick={() => removeToast(t.id)}
          style={{
            background: t.type === 'error' ? '#fee' : t.type === 'success' ? '#e9f7ef' : '#eef5f7',
            color: t.type === 'error' ? '#a33' : t.type === 'success' ? '#1f7a4d' : '#2b4a52',
            border: '1px solid ' + (t.type === 'error' ? '#f5c2c7' : t.type === 'success' ? '#b7e1cd' : '#cfe3e8'),
            boxShadow: '0 6px 24px rgba(0,0,0,0.08)',
            padding: '10px 12px',
            borderRadius: 10,
            minWidth: 240,
            maxWidth: 600,
            cursor: 'pointer',
          }}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}


