'use client';
import React from 'react';

interface PaginationProps {
  current: number;
  total: number;
  pageSize?: number;
  onChange: (page: number) => void;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  onPageSizeChange?: (size: number) => void;
  className?: string;
}

export default function Pagination({
  current,
  total,
  pageSize = 10,
  onChange,
  showSizeChanger = false,
  pageSizeOptions = [10, 20, 50],
  onPageSizeChange,
  className = '',
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const getVisiblePages = (): (number | '...')[] => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    const pages: (number | '...')[] = [1];
    if (current > 3) pages.push('...');
    for (let i = Math.max(2, current - 1); i <= Math.min(totalPages - 1, current + 1); i++) {
      pages.push(i);
    }
    if (current < totalPages - 2) pages.push('...');
    pages.push(totalPages);
    return pages;
  };

  const btnStyle = (active = false, disabled = false): React.CSSProperties => ({
    width: 32,
    height: 32,
    borderRadius: 'var(--ae-radius-sm)',
    border: active ? '1px solid var(--ae-accent-olive)' : '1px solid var(--ae-line)',
    background: active ? 'rgba(122, 138, 106, 0.1)' : 'transparent',
    color: disabled ? 'var(--ae-muted)' : active ? 'var(--ae-accent-olive)' : 'var(--ae-text)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: 13,
    fontWeight: active ? 600 : 400,
    display: 'grid',
    placeItems: 'center',
    opacity: disabled ? 0.5 : 1,
    transition: 'all 180ms ease',
  });

  return (
    <nav
      role="navigation"
      aria-label="Pagination"
      className={className}
      style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}
    >
      <button
        type="button"
        aria-label="Previous page"
        disabled={current <= 1}
        onClick={() => onChange(current - 1)}
        style={btnStyle(false, current <= 1)}
      >
        ‹
      </button>
      {getVisiblePages().map((page, i) =>
        page === '...' ? (
          <span key={`ellipsis-${i}`} aria-hidden="true" style={{ width: 32, textAlign: 'center', color: 'var(--ae-muted)', fontSize: 13 }}>…</span>
        ) : (
          <button
            key={page}
            type="button"
            aria-label={`Page ${page}`}
            aria-current={page === current ? 'page' : undefined}
            onClick={() => onChange(page)}
            style={btnStyle(page === current)}
          >
            {page}
          </button>
        )
      )}
      <button
        type="button"
        aria-label="Next page"
        disabled={current >= totalPages}
        onClick={() => onChange(current + 1)}
        style={btnStyle(false, current >= totalPages)}
      >
        ›
      </button>
      {showSizeChanger && onPageSizeChange && (
        <select
          aria-label="Items per page"
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          style={{
            marginLeft: 8,
            padding: '6px 8px',
            borderRadius: 'var(--ae-radius-sm)',
            border: '1px solid var(--ae-line)',
            background: 'var(--ae-panel)',
            color: 'var(--ae-text)',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>{size} / page</option>
          ))}
        </select>
      )}
    </nav>
  );
}
