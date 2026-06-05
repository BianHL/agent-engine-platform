'use client';
import React from 'react';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  className?: string;
}

export default function ToggleSwitch({ checked, onChange, label, className = '' }: ToggleSwitchProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      onChange(!checked);
    }
  };

  return (
    <label
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        cursor: 'pointer',
      }}
    >
      <div
        role="switch"
        aria-checked={checked}
        tabIndex={0}
        onClick={() => onChange(!checked)}
        onKeyDown={handleKeyDown}
        className="ae-toggle-track"
        style={{
          width: 44,
          height: 24,
          borderRadius: 'var(--ae-radius-full)',
          background: checked ? 'var(--ae-accent-olive)' : 'var(--ae-line)',
          position: 'relative',
          cursor: 'pointer',
          transition: 'background 200ms ease, box-shadow 200ms ease',
          flexShrink: 0,
          outline: 'none',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 2,
            left: checked ? 22 : 2,
            width: 20,
            height: 20,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.95)',
            boxShadow: '0 2px 6px rgba(0,0,0,.15)',
            transition: 'transform 200ms ease',
          }}
        />
      </div>
      {label && (
        <span style={{ fontSize: 13, color: 'var(--ae-muted)' }}>{label}</span>
      )}
      <style jsx>{`
        .ae-toggle-track:focus-visible {
          box-shadow: 0 0 0 3px rgba(122, 138, 106, 0.3);
        }
      `}</style>
    </label>
  );
}
