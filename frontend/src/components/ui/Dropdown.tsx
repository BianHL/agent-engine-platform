'use client';
import React, { useState, useRef, useEffect, useCallback } from 'react';

interface DropdownItem {
  key: string;
  label: string;
  disabled?: boolean;
}

interface DropdownProps {
  children: React.ReactNode;
  items: DropdownItem[];
  onSelect: (key: string) => void;
}

export default function Dropdown({ children, items, onSelect }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const [focusIndex, setFocusIndex] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const enabledIndices = items
    .map((item, i) => (item.disabled ? -1 : i))
    .filter((i) => i >= 0);

  const closeMenu = useCallback(() => {
    setOpen(false);
    setFocusIndex(-1);
    triggerRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        closeMenu();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [closeMenu]);

  // Focus the menu item when focusIndex changes
  useEffect(() => {
    if (open && focusIndex >= 0 && menuRef.current) {
      const menuItems = menuRef.current.querySelectorAll('[role="menuitem"]');
      (menuItems[focusIndex] as HTMLElement)?.focus();
    }
  }, [open, focusIndex]);

  const handleSelect = (item: DropdownItem) => {
    if (!item.disabled) {
      onSelect(item.key);
      closeMenu();
    }
  };

  const handleTriggerKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
      case ' ':
      case 'ArrowDown':
        e.preventDefault();
        setOpen(true);
        setFocusIndex(enabledIndices[0] ?? -1);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setOpen(true);
        setFocusIndex(enabledIndices[enabledIndices.length - 1] ?? -1);
        break;
    }
  };

  const handleMenuKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        closeMenu();
        break;
      case 'ArrowDown': {
        e.preventDefault();
        const currentPos = enabledIndices.indexOf(focusIndex);
        const nextPos = (currentPos + 1) % enabledIndices.length;
        setFocusIndex(enabledIndices[nextPos]);
        break;
      }
      case 'ArrowUp': {
        e.preventDefault();
        const currentPos = enabledIndices.indexOf(focusIndex);
        const prevPos = (currentPos - 1 + enabledIndices.length) % enabledIndices.length;
        setFocusIndex(enabledIndices[prevPos]);
        break;
      }
      case 'Home':
        e.preventDefault();
        setFocusIndex(enabledIndices[0] ?? -1);
        break;
      case 'End':
        e.preventDefault();
        setFocusIndex(enabledIndices[enabledIndices.length - 1] ?? -1);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (focusIndex >= 0) handleSelect(items[focusIndex]);
        break;
      case 'Tab':
        closeMenu();
        break;
    }
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        ref={triggerRef}
        type="button"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => {
          setOpen(!open);
          if (!open) setFocusIndex(enabledIndices[0] ?? -1);
        }}
        onKeyDown={handleTriggerKeyDown}
        style={{
          cursor: 'pointer',
          background: 'none',
          border: 'none',
          padding: 0,
          font: 'inherit',
          color: 'inherit',
        }}
      >
        {children}
      </button>
      {open && (
        <div
          ref={menuRef}
          role="menu"
          onKeyDown={handleMenuKeyDown}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: 4,
            minWidth: 160,
            background: 'var(--ae-surface)',
            borderRadius: 'var(--ae-radius-md)',
            boxShadow: '0 6px 16px rgba(0,0,0,.12)',
            border: '1px solid var(--ae-line)',
            padding: '4px 0',
            zIndex: 1000,
          }}
        >
          {items.map((item, index) => (
            <div
              key={item.key}
              role="menuitem"
              tabIndex={-1}
              aria-disabled={item.disabled || undefined}
              onClick={() => handleSelect(item)}
              style={{
                padding: '8px 12px',
                fontSize: 13,
                color: item.disabled ? 'var(--ae-muted)' : 'var(--ae-text)',
                cursor: item.disabled ? 'not-allowed' : 'pointer',
                opacity: item.disabled ? 0.5 : 1,
                transition: 'background 150ms ease',
                outline: 'none',
              }}
              onMouseEnter={(e) => {
                if (!item.disabled) {
                  e.currentTarget.style.background = 'var(--ae-bg)';
                }
                setFocusIndex(index);
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
              }}
            >
              {item.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
