'use client';
import React from 'react';

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'danger' | 'info' | 'processing';
  text?: string;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, text, size = 'md' }: StatusBadgeProps) {
  const dotColors = {
    success: 'var(--ae-success)',
    warning: 'var(--ae-warning)',
    danger: 'var(--ae-danger)',
    info: 'var(--ae-accent-olive)',
    processing: 'var(--ae-warning)',
  };

  const glowColors = {
    success: 'rgba(111,155,124,.15)',
    warning: 'rgba(208,164,93,.15)',
    danger: 'rgba(196,122,110,.15)',
    info: 'rgba(122,138,106,.15)',
    processing: 'rgba(208,164,93,.15)',
  };

  const displayText = text || status.charAt(0).toUpperCase() + status.slice(1);
  const padding = size === 'sm' ? '4px 10px' : '6px 12px';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding,
        borderRadius: 'var(--ae-radius-full)',
        fontSize: size === 'sm' ? 11 : 12,
        fontWeight: 600,
        border: '1px solid var(--ae-line)',
        background: 'var(--ae-panel)',
      }}
    >
      <span
        className={status === 'processing' ? 'status-pulse' : ''}
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          background: dotColors[status],
          boxShadow: `0 0 0 3px ${glowColors[status]}`,
          display: 'inline-block',
        }}
      />
      {displayText}
      <style jsx>{`
        .status-pulse {
          animation: pulseSoft 1.5s ease-in-out infinite;
        }
      `}</style>
    </span>
  );
}
