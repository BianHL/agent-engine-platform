'use client';
import { useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { message } from 'antd';

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  description: string;
  action: () => void;
  preventDefault?: boolean;
}

interface ShortcutGroup {
  name: string;
  shortcuts: ShortcutConfig[];
}

const DEFAULT_SHORTCUTS: ShortcutGroup[] = [
  {
    name: 'Navigation',
    shortcuts: [
      { key: 'd', ctrl: true, description: 'Go to Dashboard', action: () => {}, preventDefault: true },
      { key: 'a', ctrl: true, description: 'Go to Agents', action: () => {}, preventDefault: true },
      { key: 'k', ctrl: true, description: 'Go to Knowledge', action: () => {}, preventDefault: true },
      { key: 'w', ctrl: true, description: 'Go to Workflows', action: () => {}, preventDefault: true },
      { key: 't', ctrl: true, description: 'Go to Tools', action: () => {}, preventDefault: true },
    ],
  },
  {
    name: 'Actions',
    shortcuts: [
      { key: 'n', ctrl: true, description: 'Create New', action: () => {}, preventDefault: true },
      { key: 's', ctrl: true, description: 'Save', action: () => {}, preventDefault: true },
      { key: 'z', ctrl: true, description: 'Undo', action: () => {}, preventDefault: true },
      { key: 'z', ctrl: true, shift: true, description: 'Redo', action: () => {}, preventDefault: true },
    ],
  },
  {
    name: 'General',
    shortcuts: [
      { key: '/', ctrl: true, description: 'Show Shortcuts', action: () => {}, preventDefault: true },
      { key: 'Escape', description: 'Close Modal/Panel', action: () => {} },
      { key: 'k', meta: true, description: 'Command Palette', action: () => {}, preventDefault: true },
    ],
  },
];

export function useKeyboardShortcuts(customShortcuts?: ShortcutGroup[]) {
  const router = useRouter();
  const shortcutsRef = useRef<ShortcutGroup[]>([]);

  // Merge default shortcuts with custom ones
  useEffect(() => {
    const navigationShortcuts = DEFAULT_SHORTCUTS.find(g => g.name === 'Navigation');
    if (navigationShortcuts) {
      navigationShortcuts.shortcuts = [
        { ...navigationShortcuts.shortcuts[0], action: () => router.push('/dashboard') },
        { ...navigationShortcuts.shortcuts[1], action: () => router.push('/agents') },
        { ...navigationShortcuts.shortcuts[2], action: () => router.push('/knowledge') },
        { ...navigationShortcuts.shortcuts[3], action: () => router.push('/workflows') },
        { ...navigationShortcuts.shortcuts[4], action: () => router.push('/tools') },
      ];
    }

    const generalShortcuts = DEFAULT_SHORTCUTS.find(g => g.name === 'General');
    if (generalShortcuts) {
      const showShortcuts = generalShortcuts.shortcuts.find(s => s.key === '/');
      if (showShortcuts) {
        showShortcuts.action = () => {
          message.info('Keyboard Shortcuts: Ctrl+D (Dashboard), Ctrl+A (Agents), Ctrl+K (Knowledge), Ctrl+W (Workflows), Ctrl+T (Tools)');
        };
      }
    }

    shortcutsRef.current = customShortcuts || DEFAULT_SHORTCUTS;
  }, [router, customShortcuts]);

  // Handle keyboard events
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const target = event.target as HTMLElement;
    const tagName = target.tagName.toLowerCase();

    // Don't trigger shortcuts when typing in input fields
    if (tagName === 'input' || tagName === 'textarea' || tagName === 'select' || target.isContentEditable) {
      return;
    }

    const isCtrl = event.ctrlKey || event.metaKey;
    const isShift = event.shiftKey;
    const isAlt = event.altKey;

    for (const group of shortcutsRef.current) {
      for (const shortcut of group.shortcuts) {
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = shortcut.ctrl ? isCtrl : !isCtrl;
        const shiftMatch = shortcut.shift ? isShift : !isShift;
        const altMatch = shortcut.alt ? isAlt : !isAlt;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }
          shortcut.action();
          return;
        }
      }
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    shortcuts: shortcutsRef.current,
    getShortcutList: () => {
      return shortcutsRef.current.flatMap(group =>
        group.shortcuts.map(shortcut => ({
          group: group.name,
          ...shortcut,
          display: formatShortcut(shortcut),
        }))
      );
    },
  };
}

function formatShortcut(shortcut: ShortcutConfig): string {
  const parts: string[] = [];
  if (shortcut.ctrl || shortcut.meta) parts.push('Ctrl');
  if (shortcut.shift) parts.push('Shift');
  if (shortcut.alt) parts.push('Alt');
  parts.push(shortcut.key.toUpperCase());
  return parts.join('+');
}

// Hook for workflow-specific shortcuts
export function useWorkflowShortcuts({
  onUndo,
  onRedo,
  onDelete,
  onSave,
  onRun,
}: {
  onUndo?: () => void;
  onRedo?: () => void;
  onDelete?: () => void;
  onSave?: () => void;
  onRun?: () => void;
}) {
  const workflowShortcuts: ShortcutGroup[] = [
    {
      name: 'Workflow',
      shortcuts: [
        { key: 'z', ctrl: true, description: 'Undo', action: onUndo || (() => {}), preventDefault: true },
        { key: 'z', ctrl: true, shift: true, description: 'Redo', action: onRedo || (() => {}), preventDefault: true },
        { key: 'Delete', description: 'Delete Selected', action: onDelete || (() => {}) },
        { key: 'Backspace', description: 'Delete Selected', action: onDelete || (() => {}) },
        { key: 's', ctrl: true, description: 'Save Workflow', action: onSave || (() => {}), preventDefault: true },
        { key: 'r', ctrl: true, description: 'Run Workflow', action: onRun || (() => {}), preventDefault: true },
      ],
    },
  ];

  return useKeyboardShortcuts(workflowShortcuts);
}

// Hook for chat shortcuts
export function useChatShortcuts({
  onSend,
  onStop,
  onClear,
}: {
  onSend?: () => void;
  onStop?: () => void;
  onClear?: () => void;
}) {
  const chatShortcuts: ShortcutGroup[] = [
    {
      name: 'Chat',
      shortcuts: [
        { key: 'Enter', ctrl: true, description: 'Send Message', action: onSend || (() => {}), preventDefault: true },
        { key: 'Escape', description: 'Stop Generation', action: onStop || (() => {}) },
        { key: 'l', ctrl: true, description: 'Clear Chat', action: onClear || (() => {}), preventDefault: true },
      ],
    },
  ];

  return useKeyboardShortcuts(chatShortcuts);
}
