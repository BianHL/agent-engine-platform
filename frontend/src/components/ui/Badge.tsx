'use client';
import React from 'react';

interface BadgeProps {
  children?: React.ReactNode;
  count?: number;
  variant?: 'count' | 'dot';
  color?: 'default' | 'success' | 'warning' | 'error';
  overflowCount?: number;
  showZero?: boolean;
  'aria-label'?: string;
}

const colorMap = {
  default: 'var(--ae-accent-olive)',
  success: 'var(--ae-success)',
  warning: 'var(--ae-warning)',
  error: 'var(--ae-danger)',
};

export default function Badge({
  children,
  count = 0,
  variant = 'count',
  color = 'default',
  overflowCount = 99,
  showZero = false,
  'aria-label': ariaLabel,
}: BadgeProps) {
  const displayCount = count > overflowCount ? `${overflowCount}+` : count;
  const showBadge = variant === 'dot' || count > 0 || showZero;
  const label = ariaLabel || (variant === 'dot' ? 'New notification' : `${count} notifications`);

  const badgeStyle: React.CSSProperties = variant === 'dot'
    ? {
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: colorMap[color],
        position: 'absolute',
        top: -4,
        right: -4,
        border: '2px solid var(--ae-bg)',
      }
    : {
        minWidth: 20,
        height: 20,
        padding: '0 6px',
        borderRadius: 10,
        background: colorMap[color],
        color: '#fff',
        fontSize: 12,
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'absolute',
        top: -10,
        right: -10,
        border: '2px solid var(--ae-bg)',
        lineHeight: 1,
      };

  if (!children) {
    return showBadge ? (
      <span aria-label={label} style={{ position: 'relative', display: 'inline-flex' }}>
        <span style={badgeStyle}>{variant === 'count' ? displayCount : null}</span>
      </span>
    ) : null;
  }

  return (
    <span style={{ position: 'relative', display: 'inline-flex' }}>
      {children}
      {showBadge && (
        <span aria-label={label} style={badgeStyle}>
          {variant === 'count' ? displayCount : null}
        </span>
      )}
    </span>
  );
}
