'use client';
import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
  lines?: number;
  animate?: boolean;
  className?: string;
}

export default function Skeleton({
  width,
  height,
  variant = 'text',
  lines = 1,
  animate = true,
  className = '',
}: SkeletonProps) {
  const baseStyle: React.CSSProperties = {
    background: 'linear-gradient(90deg, var(--ae-line) 25%, rgba(86, 68, 54, 0.06) 50%, var(--ae-line) 75%)',
    backgroundSize: '200% 100%',
    borderRadius: variant === 'circular' ? '50%' : 'var(--ae-radius-sm)',
    width: width || (variant === 'circular' ? height : '100%'),
    height: height || (variant === 'text' ? 16 : height),
    animation: animate ? 'skeleton-shimmer 1.5s ease-in-out infinite' : 'none',
  };

  if (variant === 'text' && lines > 1) {
    return (
      <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            aria-hidden="true"
            style={{
              ...baseStyle,
              width: i === lines - 1 ? '60%' : (width || '100%'),
            }}
          />
        ))}
        <style jsx>{`
          @keyframes skeleton-shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
          }
        `}</style>
      </div>
    );
  }

  return (
    <>
      <div
        aria-hidden="true"
        className={className}
        style={baseStyle}
      />
      <style jsx>{`
        @keyframes skeleton-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </>
  );
}
