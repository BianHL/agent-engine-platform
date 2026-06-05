'use client';
import React from 'react';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  label?: string;
  hint?: string;
  error?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  allowClear?: boolean;
  className?: string;
}

export default function Input({
  label,
  hint,
  error,
  prefix,
  suffix,
  allowClear = false,
  className = '',
  value,
  onChange,
  ...props
}: InputProps) {
  const inputId = React.useId();
  const errorId = error ? `${inputId}-error` : undefined;
  const hintId = hint && !error ? `${inputId}-hint` : undefined;
  const describedBy = errorId || hintId;

  const hasAdornment = prefix || suffix || allowClear;
  const showClear = allowClear && value;

  const handleClear = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onChange) {
      onChange({ target: { value: '' } } as React.ChangeEvent<HTMLInputElement>);
    }
  };

  const inputElement = (
    <input
      {...props}
      id={inputId}
      value={value}
      onChange={onChange}
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
        flex: 1,
        minWidth: 0,
      }}
    />
  );

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label htmlFor={inputId} style={{ fontSize: 12, fontWeight: 600, color: 'var(--ae-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {label}
        </label>
      )}
      {hasAdornment ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          borderRadius: 14,
          border: `1px solid ${error ? 'var(--ae-danger)' : 'var(--ae-line)'}`,
          background: 'var(--ae-panel)',
          padding: '0 4px',
        }}>
          {prefix && <span style={{ color: 'var(--ae-muted)', fontSize: 14, flexShrink: 0 }}>{prefix}</span>}
          <input
            {...props}
            id={inputId}
            value={value}
            onChange={onChange}
            aria-describedby={describedBy}
            aria-invalid={!!error}
            className={`ae-input ${error ? 'ae-input-error' : ''}`}
            style={{
              padding: '12px 4px',
              border: 'none',
              background: 'transparent',
              color: 'var(--ae-text)',
              font: 'inherit',
              fontSize: 14,
              outline: 'none',
              width: '100%',
              flex: 1,
              minWidth: 0,
            }}
          />
          {showClear && (
            <button
              type="button"
              aria-label="Clear"
              onClick={handleClear}
              style={{
                width: 20,
                height: 20,
                borderRadius: '50%',
                border: 'none',
                background: 'var(--ae-line)',
                color: 'var(--ae-muted)',
                cursor: 'pointer',
                display: 'grid',
                placeItems: 'center',
                fontSize: 11,
                flexShrink: 0,
              }}
            >
              ✕
            </button>
          )}
          {suffix && <span style={{ color: 'var(--ae-muted)', fontSize: 14, flexShrink: 0 }}>{suffix}</span>}
        </div>
      ) : (
        inputElement
      )}
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
