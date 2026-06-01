'use client';
import React from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
  placeholder?: string;
  className?: string;
}

export default function Select({
  options,
  value,
  onChange,
  label,
  placeholder = 'Select...',
  className = '',
}: SelectProps) {
  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--ae-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        style={{
          padding: '12px 14px',
          borderRadius: 14,
          border: '1px solid var(--ae-line)',
          background: 'var(--ae-panel)',
          color: 'var(--ae-text)',
          font: 'inherit',
          fontSize: 14,
          outline: 'none',
          cursor: 'pointer',
          transition: 'border-color 180ms ease, box-shadow 180ms ease',
          width: '100%',
          appearance: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2326221e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 14px center',
          paddingRight: 40,
        }}
      >
        <option value="" disabled>{placeholder}</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      <style jsx>{`
        select:focus {
          border-color: var(--ae-accent-olive) !important;
          box-shadow: 0 0 0 3px rgba(122, 138, 106, 0.12);
        }
      `}</style>
    </div>
  );
}
