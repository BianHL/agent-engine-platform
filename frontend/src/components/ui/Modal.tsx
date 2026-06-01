'use client';
import React from 'react';

interface ModalProps {
  open: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  footer?: React.ReactNode;
  className?: string;
}

export default function Modal({
  open,
  title,
  children,
  onClose,
  footer,
  className = '',
}: ModalProps) {
  if (!open) return null;

  return (
    <div
      className="modal-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,.35)',
        backdropFilter: 'blur(4px)',
        zIndex: 999,
        display: 'grid',
        placeItems: 'center',
        opacity: open ? 1 : 0,
        transition: 'opacity 300ms ease',
      }}
    >
      <div
        className={`modal-content ${className}`}
        style={{
          width: '90%',
          maxWidth: 480,
          borderRadius: 'var(--ae-radius-xl)',
          border: '1px solid var(--ae-line)',
          background: 'linear-gradient(180deg, var(--ae-panel-strong), var(--ae-panel))',
          boxShadow: 'var(--ae-shadow)',
          padding: 28,
          transform: open ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.97)',
          transition: 'transform 300ms cubic-bezier(.2,1,.2,1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <h3 style={{ margin: 0, fontFamily: 'var(--ae-font-family-serif)', fontSize: 22 }}>{title}</h3>
          <button
            onClick={onClose}
            style={{
              width: 32, height: 32, borderRadius: 'var(--ae-radius-sm)',
              border: '1px solid var(--ae-line)',
              background: 'transparent',
              cursor: 'pointer', color: 'var(--ae-muted)',
              display: 'grid', placeItems: 'center',
              fontSize: 16,
            }}
          >
            ✕
          </button>
        </div>
        <div style={{ color: 'var(--ae-muted)', fontSize: 14, lineHeight: 1.7 }}>{children}</div>
        {footer && (
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
