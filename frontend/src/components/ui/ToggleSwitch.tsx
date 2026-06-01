'use client';
import React from 'react';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  className?: string;
}

export default function ToggleSwitch({ checked, onChange, label, className = '' }: ToggleSwitchProps) {
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
        onClick={() => onChange(!checked)}
        style={{
          width: 44,
          height: 24,
          borderRadius: 'var(--ae-radius-full)',
          background: checked ? 'var(--ae-accent-olive)' : 'var(--ae-line)',
          position: 'relative',
          cursor: 'pointer',
          transition: 'background 200ms ease',
          flexShrink: 0,
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
    </label>
  );
}
