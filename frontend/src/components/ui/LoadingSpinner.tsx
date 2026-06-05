'use client';
import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large';
  tip?: string;
  fullScreen?: boolean;
}

const sizeMap = { small: 16, default: 24, large: 36 };

export default function LoadingSpinner({ size = 'large', tip, fullScreen = false }: LoadingSpinnerProps) {
  const px = sizeMap[size];

  const spinner = (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
      <div
        role="status"
        aria-label={tip || 'Loading'}
        style={{
          width: px, height: px,
          border: '2px solid var(--ae-border, #e5e1d8)',
          borderTopColor: 'var(--ae-accent, #b8956a)',
          borderRadius: '50%',
          animation: 'ae-spin 0.8s linear infinite',
        }}
      />
      {tip && (
        <span style={{ fontSize: 14, color: 'var(--ae-text-secondary, #6b7280)' }}>
          {tip}
        </span>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        height: '100%', minHeight: 200,
      }}>
        {spinner}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
      {spinner}
    </div>
  );
}
