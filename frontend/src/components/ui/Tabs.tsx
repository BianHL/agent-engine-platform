'use client';
import React from 'react';

interface TabItem {
  key: string;
  label: string;
  disabled?: boolean;
}

interface TabsProps {
  items: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
  children?: React.ReactNode;
}

export default function Tabs({ items, activeKey, onChange, children }: TabsProps) {
  return (
    <div>
      <div
        role="tablist"
        style={{
          display: 'flex',
          gap: 0,
          borderBottom: '1px solid var(--ae-line)',
        }}
      >
        {items.map((item) => {
          const isActive = item.key === activeKey;
          return (
            <button
              key={item.key}
              role="tab"
              aria-selected={isActive}
              aria-disabled={item.disabled || undefined}
              tabIndex={isActive ? 0 : -1}
              onClick={() => !item.disabled && onChange(item.key)}
              style={{
                padding: '10px 16px',
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                color: item.disabled
                  ? 'var(--ae-muted)'
                  : isActive
                    ? 'var(--ae-accent-olive)'
                    : 'var(--ae-text-secondary)',
                background: 'transparent',
                border: 'none',
                borderBottom: `2px solid ${isActive ? 'var(--ae-accent-olive)' : 'transparent'}`,
                cursor: item.disabled ? 'not-allowed' : 'pointer',
                opacity: item.disabled ? 0.5 : 1,
                transition: 'all 180ms ease',
                outline: 'none',
              }}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      <div role="tabpanel" style={{ paddingTop: 16 }}>
        {children}
      </div>
    </div>
  );
}
