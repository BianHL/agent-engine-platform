'use client';
import React from 'react';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'hero' | 'compact';
  decorative?: boolean;
  hover?: boolean;
  className?: string;
}

export default function Card({
  children,
  variant = 'default',
  decorative = false,
  hover = true,
  className = '',
}: CardProps) {
  const radius = variant === 'compact' ? 'var(--ae-radius-lg)' : 'var(--ae-radius-xl)';
  const padding = variant === 'compact' ? '16px' : variant === 'hero' ? '28px' : '20px';

  return (
    <div
      className={`${hover ? 'card-hover' : ''} ${className}`}
      style={{
        borderRadius: radius,
        background: 'linear-gradient(180deg, rgba(255,255,255,0.82), rgba(252,250,247,0.66))',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid var(--ae-line)',
        boxShadow: 'var(--ae-shadow-soft)',
        padding,
        position: 'relative',
        overflow: 'hidden',
        transition: 'transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease',
      }}
    >
      {decorative && (
        <div
          style={{
            position: 'absolute',
            right: -40,
            top: -30,
            width: 200,
            height: 200,
            borderRadius: 40,
            background: 'linear-gradient(135deg, rgba(126,143,122,0.16), rgba(194,154,99,0.12))',
            transform: 'rotate(12deg)',
            pointerEvents: 'none',
            animation: 'drift 12s ease-in-out infinite alternate',
          }}
        />
      )}
      <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>

      <style jsx>{`
        .card-hover:hover {
          transform: translateY(-4px);
          border-color: rgba(168, 149, 106, 0.22);
          box-shadow: 0 24px 48px rgba(58, 47, 38, 0.12);
        }
      `}</style>
    </div>
  );
}
