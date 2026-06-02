'use client';
import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  className?: string;
}

export default function Input({
  label,
  hint,
  error,
  className = '',
  ...props
}: InputProps) {
  const inputId = React.useId();
  const errorId = error ? `${inputId}-error` : undefined;
  const hintId = hint && !error ? `${inputId}-hint` : undefined;
  const describedBy = errorId || hintId;

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label htmlFor={inputId} style={{ fontSize: 12, fontWeight: 600, color: 'var(--ae-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {label}
        </label>
      )}
      <input
        {...props}
        id={inputId}
        aria-describedby={describedBy}
        aria-invalid={!!error}
        className={`ae-input ${error ? 'ae-input-error' : ''}`}
        style={{
          padding: '12px 14px',
          borderRadius: 14,
          border: `1px solid ${error ? 'var(--ae-danger)' : 'var(--ae-line)'}`,
          background: 'var(--ae-panel)',
          color: 'var(--ae-text)',
          font: 'inherit',
          fontSize: 14,
          outline: 'none',
          transition: 'border-color 180ms ease, box-shadow 180ms ease',
          width: '100%',
        }}
      />
      {error && (
        <span id={errorId} role="alert" style={{ fontSize: 12, color: 'var(--ae-danger)', marginTop: 2 }}>{error}</span>
      )}
      {hint && !error && (
        <span id={hintId} style={{ fontSize: 12, color: 'var(--ae-muted)', marginTop: 2 }}>{hint}</span>
      )}
      <style jsx>{`
        .ae-input:focus {
          border-color: var(--ae-accent-olive) !important;
          box-shadow: 0 0 0 3px rgba(122, 138, 106, 0.12);
        }
        .ae-input-error:focus {
          border-color: var(--ae-danger) !important;
          box-shadow: 0 0 0 3px rgba(196, 122, 110, 0.12);
        }
      `}</style>
    </div>
  );
}
