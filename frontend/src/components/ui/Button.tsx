'use client';
import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit';
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  className = '',
  type = 'button',
}: ButtonProps) {
  const sizeStyles = {
    sm: { padding: '8px 14px', fontSize: 12, borderRadius: 'var(--ae-radius-md)' },
    md: { padding: '12px 16px', fontSize: 13, borderRadius: 'var(--ae-radius-md)' },
    lg: { padding: '14px 20px', fontSize: 14, borderRadius: 'var(--ae-radius-lg)' },
  };

  const variantStyles = {
    primary: {
      background: 'linear-gradient(135deg, #b8956a, #a08060 52%, #8b9a6d)',
      color: 'rgba(255,255,255,0.95)',
      border: 'none',
      boxShadow: '0 14px 28px rgba(168,149,106,.18)',
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
      boxShadow: '0 10px 20px rgba(196,122,110,.15)',
    },
  };

  const s = sizeStyles[size];
  const v = variantStyles[variant];

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`ae-btn ${className}`}
      style={{
        ...s,
        ...v,
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'transform 180ms ease, box-shadow 180ms ease, background 180ms ease',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
      }}
    >
      {children}
      <style jsx>{`
        .ae-btn:hover:not(:disabled) {
          transform: translateY(-1px);
        }
        .ae-btn:active:not(:disabled) {
          transform: translateY(0.5px);
        }
      `}</style>
    </button>
  );
}
