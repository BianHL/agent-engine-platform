'use client';
import React from 'react';
import { SearchOutlined } from '@ant-design/icons';

interface SearchInputProps {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function SearchInput({
  value,
  onChange,
  placeholder = 'Search...',
  className = '',
}: SearchInputProps) {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 14px',
        borderRadius: 'var(--ae-radius-lg)',
        border: '1px solid var(--ae-line)',
        background: 'rgba(255, 255, 255, 0.50)',
        backdropFilter: 'blur(10px)',
        transition: 'all 180ms ease',
      }}
    >
      <SearchOutlined style={{ fontSize: 14, color: 'var(--ae-muted)' }} />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        style={{
          border: 'none',
          background: 'transparent',
          outline: 'none',
          flex: 1,
          font: 'inherit',
          fontSize: 13,
          color: 'var(--ae-text)',
        }}
      />
    </div>
  );
}
