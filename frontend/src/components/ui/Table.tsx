'use client';
import React from 'react';

interface Column<T> {
  key: string;
  title: string;
  render?: (item: T) => React.ReactNode;
  width?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
  emptyMessage?: string;
}

export default function Table<T extends Record<string, unknown>>({
  data,
  columns,
  className = '',
  emptyMessage = 'No data',
}: TableProps<T>) {
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
                }}
              >
                {col.title}
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
      <style jsx>{`
        .table-row:hover {
          background: rgba(122, 138, 106, 0.04);
        }
      `}</style>
    </div>
  );
}
