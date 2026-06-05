'use client';
import React, { useEffect, useRef } from 'react';

interface ConfirmModalProps {
  open: boolean;
  title: string;
  content: React.ReactNode;
  confirmLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  okText?: string;
  cancelText?: string;
  danger?: boolean;
}

export default function ConfirmModal({
  open,
  title,
  content,
  confirmLoading = false,
  onConfirm,
  onCancel,
  okText = 'OK',
  cancelText = 'Cancel',
  danger = false,
}: ConfirmModalProps) {
  const confirmRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setTimeout(() => confirmRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
      }
      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = Array.from(
          dialogRef.current.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          )
        ).filter((el) => !el.matches(':disabled') && el.offsetParent !== null);

        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      className="ae-confirm-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.45)',
        display: 'flex', justifyContent: 'center', alignItems: 'center',
      }}
    >
      <div
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--ae-bg-card, #fff)',
          borderRadius: 'var(--ae-radius-lg, 16px)',
          padding: '24px',
          maxWidth: 400, width: '90%',
          boxShadow: 'var(--ae-shadow-modal, 0 20px 60px rgba(0,0,0,0.15))',
        }}
      >
        <h3 style={{
          margin: '0 0 12px',
          fontSize: 16, fontWeight: 600,
          color: 'var(--ae-text-primary, #1a1a2e)',
        }}>
          {title}
        </h3>
        <div style={{
          marginBottom: 24,
          fontSize: 14,
          color: 'var(--ae-text-secondary, #6b7280)',
          lineHeight: 1.6,
        }}>
          {content}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button
            onClick={onCancel}
            disabled={confirmLoading}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--ae-radius-md, 8px)',
              border: '1px solid var(--ae-border, #e5e1d8)',
              background: 'var(--ae-bg-card, #fff)',
              color: 'var(--ae-text-primary, #1a1a2e)',
              fontSize: 14, cursor: 'pointer',
              opacity: confirmLoading ? 0.6 : 1,
            }}
          >
            {cancelText}
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            disabled={confirmLoading}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--ae-radius-md, 8px)',
              border: 'none',
              background: danger
                ? 'var(--ae-danger, #c47a6e)'
                : 'var(--ae-accent, #b8956a)',
              color: '#fff',
              fontSize: 14, cursor: 'pointer',
              opacity: confirmLoading ? 0.6 : 1,
            }}
          >
            {confirmLoading ? '…' : okText}
          </button>
        </div>
      </div>
    </div>
  );
}
