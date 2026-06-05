'use client';
import React, { useState } from 'react';

type AlertType = 'info' | 'success' | 'warning' | 'error';

interface AlertProps {
  type?: AlertType;
  message: string;
  description?: string;
  closable?: boolean;
  onClose?: () => void;
  showIcon?: boolean;
  className?: string;
}

const typeConfig: Record<AlertType, { bg: string; border: string; color: string; icon: string }> = {
  info: {
    bg: 'rgba(122, 138, 106, 0.08)',
    border: 'rgba(122, 138, 106, 0.25)',
    color: 'var(--ae-accent-olive)',
    icon: 'ℹ',
  },
  success: {
    bg: 'rgba(111, 155, 124, 0.08)',
    border: 'rgba(111, 155, 124, 0.25)',
    color: 'var(--ae-success)',
    icon: '✓',
  },
  warning: {
    bg: 'rgba(208, 164, 93, 0.08)',
    border: 'rgba(208, 164, 93, 0.25)',
    color: 'var(--ae-warning)',
    icon: '!',
  },
  error: {
    bg: 'rgba(196, 122, 110, 0.08)',
    border: 'rgba(196, 122, 110, 0.25)',
    color: 'var(--ae-danger)',
    icon: '✕',
  },
};

export default function Alert({
  type = 'info',
  message,
  description,
  closable = true,
  onClose,
  showIcon = true,
  className = '',
}: AlertProps) {
  const [visible, setVisible] = useState(true);
  const config = typeConfig[type];

  if (!visible) return null;

  const handleClose = () => {
    setVisible(false);
    onClose?.();
  };

  return (
    <div
      role="alert"
      className={className}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        padding: '12px 16px',
        borderRadius: 'var(--ae-radius-md)',
        background: config.bg,
        border: `1px solid ${config.border}`,
        fontSize: 14,
        lineHeight: 1.6,
      }}
    >
      {showIcon && (
        <span
          aria-hidden="true"
          style={{
            width: 22,
            height: 22,
            borderRadius: '50%',
            display: 'grid',
            placeItems: 'center',
            fontSize: 12,
            fontWeight: 700,
            background: config.bg,
            color: config.color,
            border: `1px solid ${config.border}`,
            flexShrink: 0,
            marginTop: 1,
          }}
        >
          {config.icon}
        </span>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, color: 'var(--ae-text)' }}>{message}</div>
        {description && (
          <div style={{ color: 'var(--ae-muted)', marginTop: 4, fontSize: 13 }}>{description}</div>
        )}
      </div>
      {closable && (
        <button
          type="button"
          aria-label="Close alert"
          onClick={handleClose}
          style={{
            width: 24,
            height: 24,
            borderRadius: 'var(--ae-radius-sm)',
            border: 'none',
            background: 'transparent',
            color: 'var(--ae-muted)',
            cursor: 'pointer',
            display: 'grid',
            placeItems: 'center',
            fontSize: 14,
            flexShrink: 0,
          }}
        >
          ✕
        </button>
      )}
    </div>
  );
}
