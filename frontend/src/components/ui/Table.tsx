'use client';
import React from 'react';

interface Column<T> {
  key: string;
  title: string;
  render?: (item: T) => React.ReactNode;
  width?: string;
  sortable?: boolean;
}

type SortDirection = 'asc' | 'desc';

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
  emptyMessage?: string;
  loading?: boolean;
  onSort?: (key: string, direction: SortDirection) => void;
  sortKey?: string;
  sortDirection?: SortDirection;
}

export default function Table<T extends Record<string, unknown>>({
  data,
  columns,
  className = '',
  emptyMessage = 'No data',
  loading = false,
  onSort,
  sortKey,
  sortDirection = 'asc',
}: TableProps<T>) {
  const handleSort = (key: string) => {
    if (!onSort) return;
    const nextDir = sortKey === key && sortDirection === 'asc' ? 'desc' : 'asc';
    onSort(key, nextDir);
  };

  const renderSortIndicator = (colKey: string, colSortable?: boolean) => {
    if (!colSortable) return null;
    const isActive = sortKey === colKey;
    const arrow = isActive ? (sortDirection === 'asc' ? '↑' : '↓') : '↕';
    return <span aria-hidden="true" style={{ marginLeft: 4, opacity: isActive ? 1 : 0.3, fontSize: 11 }}>{arrow}</span>;
  };
  return (
    <div
      className={className}
      style={{
        border: '1px solid var(--ae-line)',
        borderRadius: 'var(--ae-radius-lg)',
        background: 'var(--ae-panel)',
        overflow: 'hidden',
        backdropFilter: 'blur(16px)',
      }}
    >
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>
            {columns.map(col => (
              <th
                key={col.key}
                role={col.sortable ? 'button' : undefined}
                tabIndex={col.sortable ? 0 : undefined}
                aria-sort={
                  col.sortable && sortKey === col.key
                    ? sortDirection === 'asc' ? 'ascending' : 'descending'
                    : col.sortable ? 'none' : undefined
                }
                onClick={col.sortable ? () => handleSort(col.key) : undefined}
                onKeyDown={col.sortable ? (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleSort(col.key);
                  }
                } : undefined}
                style={{
                  textAlign: 'left',
                  padding: '12px 16px',
                  fontSize: 11,
                  textTransform: 'uppercase',
                  letterSpacing: '0.12em',
                  color: 'var(--ae-muted)',
                  fontWeight: 600,
                  borderBottom: '1px solid var(--ae-line)',
                  background: 'rgba(255,255,255,.03)',
                  width: col.width,
                  cursor: col.sortable ? 'pointer' : 'default',
                  userSelect: col.sortable ? 'none' : undefined,
                  outline: col.sortable ? 'none' : undefined,
                }}
              >
                {col.title}
                {renderSortIndicator(col.key, col.sortable)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{
                  padding: '32px 16px',
                  textAlign: 'center',
                  color: 'var(--ae-muted)',
                  fontSize: 14,
                }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item, index) => (
              <tr
                key={index}
                className="table-row"
                style={{
                  borderBottom: '1px solid var(--ae-line)',
                  transition: 'background 180ms ease',
                }}
              >
                {columns.map(col => (
                  <td
                    key={col.key}
                    style={{
                      padding: '12px 16px',
                      color: 'var(--ae-text)',
                      borderBottom: index < data.length - 1 ? '1px solid var(--ae-line)' : 'none',
                    }}
                  >
                    {col.render ? col.render(item) : String(item[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {loading && (
        <div role="status" aria-live="polite" style={{
          padding: '16px',
          textAlign: 'center',
          color: 'var(--ae-muted)',
          fontSize: 13,
          borderTop: '1px solid var(--ae-line)',
        }}>
          Loading...
        </div>
      )}
      <style jsx>{`
        .table-row:hover {
          background: rgba(122, 138, 106, 0.04);
        }
      `}</style>
    </div>
  );
}
