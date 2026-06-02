'use client';
import React, { useEffect, useRef, useCallback } from 'react';

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
  const dialogRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<Element | null>(null);
  const titleId = React.useId();

  // Save trigger element and handle Escape
  useEffect(() => {
    if (open) {
      triggerRef.current = document.activeElement;
      // Focus first focusable element inside modal
      setTimeout(() => {
        const focusable = dialogRef.current?.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        focusable?.focus();
      }, 50);

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
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
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';

      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
        // Return focus to trigger
        if (triggerRef.current instanceof HTMLElement) {
          triggerRef.current.focus();
        }
      };
    }
  }, [open, onClose]);

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
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
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
          <h3 id={titleId} style={{ margin: 0, fontFamily: 'var(--ae-font-family-serif)', fontSize: 22 }}>{title}</h3>
          <button
            type="button"
            aria-label="Close dialog"
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
