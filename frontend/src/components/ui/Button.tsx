'use client';
import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: 'button' | 'submit';
  'aria-label'?: string;
}

const fontSizeMap = { sm: 12, md: 13, lg: 14 };

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  loading = false,
  className = '',
  type = 'button',
  'aria-label': ariaLabel,
}: ButtonProps) {
  const sizeStyles = {
    sm: { padding: '8px 14px', fontSize: 12, borderRadius: 'var(--ae-radius-md)' },
    md: { padding: '12px 16px', fontSize: 13, borderRadius: 'var(--ae-radius-md)' },
    lg: { padding: '14px 20px', fontSize: 14, borderRadius: 'var(--ae-radius-lg)' },
  };

  const variantStyles = {
    primary: {
      background: 'var(--ae-gradient-primary)',
      color: 'rgba(255,255,255,0.95)',
      border: 'none',
      boxShadow: 'var(--ae-shadow-button)',
    },
    ghost: {
      background: 'rgba(255,255,255,0.58)',
      color: 'var(--ae-text)',
      border: '1px solid var(--ae-line-strong)',
      boxShadow: 'none',
    },
    danger: {
      background: 'var(--ae-danger)',
      color: 'rgba(255,255,255,0.95)',
      border: 'none',
      boxShadow: 'var(--ae-shadow-button-danger)',
    },
  };

  const s = sizeStyles[size];
  const v = variantStyles[variant];

  const spinner = (
    <span
      aria-hidden="true"
      style={{
        width: fontSizeMap[size],
        height: fontSizeMap[size],
        border: '2px solid rgba(255,255,255,0.3)',
        borderTopColor: 'rgba(255,255,255,0.9)',
        borderRadius: '50%',
        animation: 'btn-spin 600ms linear infinite',
      }}
    />
  );

  return (
    <button
      type={type}
      onClick={loading ? undefined : onClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-disabled={disabled || loading || undefined}
      aria-busy={loading || undefined}
      className={`ae-btn ${className}`}
      style={{
        ...s,
        ...v,
        fontWeight: 600,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: loading ? 0.7 : disabled ? 0.5 : 1,
        pointerEvents: loading ? 'none' : undefined,
        transition: 'transform 180ms ease, box-shadow 180ms ease, background 180ms ease',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
      }}
    >
      {loading && spinner}
      {children}
      <style jsx>{`
        .ae-btn:hover:not(:disabled) {
          transform: translateY(-1px);
        }
        .ae-btn:active:not(:disabled) {
          transform: translateY(0.5px);
        }
        .ae-btn:focus-visible:not(:disabled) {
          outline: 2px solid var(--ae-accent);
          outline-offset: 2px;
          box-shadow: 0 0 0 4px rgba(99, 91, 255, 0.15);
        }
        @keyframes btn-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
}
