'use client';
import React from 'react';

interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
}

export default function Breadcrumb({
  items,
  separator = '/',
  className = '',
}: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className={className} style={{ fontSize: 13 }}>
      <ol style={{ display: 'flex', alignItems: 'center', gap: 6, listStyle: 'none', margin: 0, padding: 0 }}>
        {items.map((item, i) => {
          const isLast = i === items.length - 1;
          return (
            <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {i > 0 && (
                <span aria-hidden="true" style={{ color: 'var(--ae-muted)', fontSize: 11 }}>{separator}</span>
              )}
              {isLast ? (
                <span aria-current="page" style={{ color: 'var(--ae-text)', fontWeight: 600 }}>{item.label}</span>
              ) : item.href ? (
                <a
                  href={item.href}
                  onClick={item.onClick}
                  style={{ color: 'var(--ae-muted)', textDecoration: 'none', transition: 'color 180ms ease' }}
                >
                  {item.label}
                </a>
              ) : (
                <button
                  type="button"
                  onClick={item.onClick}
                  style={{
                    color: 'var(--ae-muted)',
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    font: 'inherit',
                    fontSize: 13,
                    transition: 'color 180ms ease',
                  }}
                >
                  {item.label}
                </button>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
