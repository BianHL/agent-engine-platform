'use client';
import React from 'react';

interface ProgressBarProps {
  value: number;
  className?: string;
  'aria-label'?: string;
}

export default function ProgressBar({ value, className = '', 'aria-label': ariaLabel }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={ariaLabel || 'Progress'}
      className={className}
      style={{
        height: 8,
        borderRadius: 'var(--ae-radius-full)',
        background: 'rgba(45,43,40,.07)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: '100%',
          borderRadius: 'inherit',
          width: `${clamped}%`,
          background: 'linear-gradient(90deg, var(--ae-accent-olive), var(--ae-accent-sage), var(--ae-accent-gold))',
          transition: 'width 300ms ease',
        }}
      />
    </div>
  );
}
