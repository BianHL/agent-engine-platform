'use client';
import React from 'react';
import Button from './Button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={className}
      style={{
        padding: '48px 28px',
        textAlign: 'center',
        borderRadius: 'var(--ae-radius-xl)',
        border: '1px dashed var(--ae-line-strong)',
        background: 'var(--ae-panel)',
        backdropFilter: 'blur(16px)',
      }}
    >
      {icon && (
        <div
          style={{
            width: 64,
            height: 64,
            margin: '0 auto 16px',
            borderRadius: 20,
            background: 'linear-gradient(135deg, rgba(126,143,122,.1), rgba(194,154,99,.1))',
            display: 'inline-grid',
            placeItems: 'center',
            fontSize: 28,
            color: 'var(--ae-accent-olive)',
          }}
        >
          {icon}
        </div>
      )}
      <h4
        style={{
          margin: '0 0 8px',
          fontFamily: 'var(--ae-font-family-serif)',
          fontSize: 20,
          color: 'var(--ae-text)',
        }}
      >
        {title}
      </h4>
      {description && (
        <p style={{ margin: '0 0 16px', color: 'var(--ae-muted)', fontSize: 14 }}>
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
