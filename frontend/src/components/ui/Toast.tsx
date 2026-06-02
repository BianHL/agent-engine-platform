'use client';
import React, { useState, useCallback } from 'react';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning';
}

let toastListeners: ((toasts: Toast[]) => void)[] = [];
let toasts: Toast[] = [];

function notify() {
  toastListeners.forEach(listener => listener([...toasts]));
}

export function showToast(message: string, type: 'success' | 'error' | 'warning' = 'success') {
  const id = Date.now().toString();
  toasts.push({ id, message, type });
  notify();
  const dismissMs = type === 'error' ? 8000 : 4000;
  setTimeout(() => {
    toasts = toasts.filter(t => t.id !== id);
    notify();
  }, dismissMs);
}

export function ToastContainer() {
  const [, setLocalToasts] = useState<Toast[]>([]);

  React.useEffect(() => {
    const listener = (t: Toast[]) => setLocalToasts(t);
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter(l => l !== listener);
    };
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      style={{
        position: 'fixed',
        top: 20,
        right: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        zIndex: 1000,
        pointerEvents: 'none',
      }}
    >
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}

function ToastItem({ toast }: { toast: Toast }) {
  const icons = { success: '✓', error: '✕', warning: '!' };
  const bgColors = {
    success: 'rgba(111,155,124,.12)',
    error: 'rgba(196,122,110,.12)',
    warning: 'rgba(208,164,93,.12)',
  };

  return (
    <div
      style={{
        pointerEvents: 'auto',
        padding: '14px 18px',
        borderRadius: 'var(--ae-radius-lg)',
        border: '1px solid var(--ae-line)',
        background: 'var(--ae-panel-strong)',
        boxShadow: 'var(--ae-shadow)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        fontSize: 13,
        minWidth: 280,
        animation: 'toastSlideIn 400ms cubic-bezier(.2,1,.2,1)',
      }}
    >
      <span
        style={{
          width: 28, height: 28, borderRadius: 10,
          display: 'grid', placeItems: 'center',
          fontSize: 14,
          background: bgColors[toast.type],
          color: toast.type === 'success' ? 'var(--ae-success)' : toast.type === 'error' ? 'var(--ae-danger)' : 'var(--ae-warning)',
        }}
      >
        {icons[toast.type]}
      </span>
      <span>{toast.message}</span>
    </div>
  );
}

export const toast = { show: showToast };
