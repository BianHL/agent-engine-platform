'use client';
import React from 'react';
import { motion } from 'framer-motion';

interface ProgressIndicatorProps {
  current: number;
  total: number;
}

export default function ProgressIndicator({ current, total }: ProgressIndicatorProps) {
  const progress = ((current + 1) / total) * 100;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        background: 'var(--ae-panel-strong)',
        padding: '10px 20px',
        borderRadius: 40,
        boxShadow: 'var(--ae-shadow)',
        border: '1px solid var(--ae-line)',
      }}
    >
      {/* Step dots */}
      <div style={{ display: 'flex', gap: 6 }}>
        {Array.from({ length: total }).map((_, i) => (
          <motion.div
            key={i}
            animate={{
              scale: i === current ? 1.2 : 1,
              background: i === current ? 'var(--ae-accent-olive)' : i < current ? 'var(--ae-success)' : 'var(--ae-line)',
            }}
            transition={{ duration: 0.2 }}
            style={{
              width: i === current ? 20 : 8,
              height: 8,
              borderRadius: 4,
            }}
          />
        ))}
      </div>

      {/* Step text */}
      <div style={{
        fontSize: 12,
        color: 'var(--ae-muted)',
        whiteSpace: 'nowrap',
        minWidth: 50,
        textAlign: 'right',
      }}>
        {current + 1} / {total}
      </div>

      {/* Progress bar */}
      <div style={{
        width: 60,
        height: 4,
        background: 'var(--ae-line)',
        borderRadius: 2,
        overflow: 'hidden',
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          style={{
            height: '100%',
            background: 'linear-gradient(90deg, var(--ae-accent-olive), var(--ae-accent-gold))',
            borderRadius: 2,
          }}
        />
      </div>
    </div>
  );
}
