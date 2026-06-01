'use client';
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  DashboardOutlined, RobotOutlined, DatabaseOutlined, BranchesOutlined,
  ToolOutlined, MessageOutlined, AuditOutlined, SettingOutlined,
  SearchOutlined, PlusOutlined, ThunderboltOutlined, ShopOutlined,
  EyeOutlined, ExperimentOutlined, ApiOutlined, SafetyOutlined,
  RocketOutlined, CodeOutlined, ImportOutlined, FireOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Typography } from 'antd';
const { Text } = Typography;

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: string;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export default function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const commands: CommandItem[] = useMemo(() => [
    // Navigation
    { id: 'nav-dashboard', label: 'Dashboard', icon: <DashboardOutlined />, action: () => router.push('/dashboard'), category: 'Navigate' },
    { id: 'nav-agents', label: 'Agents', icon: <RobotOutlined />, action: () => router.push('/agents'), category: 'Navigate' },
    { id: 'nav-knowledge', label: 'Knowledge Base', icon: <DatabaseOutlined />, action: () => router.push('/knowledge'), category: 'Navigate' },
    { id: 'nav-workflows', label: 'Workflows', icon: <BranchesOutlined />, action: () => router.push('/workflows'), category: 'Navigate' },
    { id: 'nav-tools', label: 'Tools', icon: <ToolOutlined />, action: () => router.push('/tools'), category: 'Navigate' },
    { id: 'nav-conversations', label: 'Conversations', icon: <MessageOutlined />, action: () => router.push('/conversations'), category: 'Navigate' },
    { id: 'nav-audit', label: 'Audit Logs', icon: <AuditOutlined />, action: () => router.push('/audit'), category: 'Navigate' },
    { id: 'nav-models', label: 'Models', icon: <SettingOutlined />, action: () => router.push('/models'), category: 'Navigate' },
    { id: 'nav-observability', label: 'Observability', icon: <EyeOutlined />, action: () => router.push('/observability'), category: 'Navigate' },
    { id: 'nav-marketplace', label: 'Marketplace', icon: <ShopOutlined />, action: () => router.push('/marketplace'), category: 'Navigate' },
    { id: 'nav-evaluations', label: 'Evaluations', icon: <ExperimentOutlined />, action: () => router.push('/evaluations'), category: 'Navigate' },

    // Create
    { id: 'create-agent', label: 'Create Agent', description: 'New AI agent configuration', icon: <PlusOutlined />, action: () => router.push('/agents/create'), category: 'Create' },
    { id: 'create-workflow', label: 'Create Workflow', description: 'Visual workflow editor', icon: <PlusOutlined />, action: () => router.push('/workflows'), category: 'Create' },
    { id: 'create-knowledge', label: 'Create Knowledge Base', description: 'Upload documents for RAG', icon: <PlusOutlined />, action: () => router.push('/knowledge'), category: 'Create' },
    { id: 'create-tool', label: 'Create Tool', description: 'Custom API tool definition', icon: <PlusOutlined />, action: () => router.push('/tools'), category: 'Create' },

    // Actions
    { id: 'run-workflow', label: 'Run Workflow', icon: <ThunderboltOutlined />, action: () => router.push('/workflows'), category: 'Actions' },
    { id: 'submit-marketplace', label: 'Submit to Marketplace', icon: <RocketOutlined />, action: () => router.push('/marketplace/submit'), category: 'Actions' },
    { id: 'prompt-editor', label: 'Prompt Editor', icon: <CodeOutlined />, action: () => router.push('/prompt-editor'), category: 'Actions' },
    { id: 'data-import', label: 'Data Import', icon: <ImportOutlined />, action: () => router.push('/import'), category: 'Actions' },
  ], [router]);

  const filteredCommands = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return commands;
    return commands.filter(cmd =>
      cmd.label.toLowerCase().includes(q) ||
      cmd.description?.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q)
    );
  }, [commands, search]);

  const groupedCommands = useMemo(() => {
    return filteredCommands.reduce((acc, cmd) => {
      if (!acc[cmd.category]) acc[cmd.category] = [];
      acc[cmd.category].push(cmd);
      return acc;
    }, {} as Record<string, CommandItem[]>);
  }, [filteredCommands]);

  useEffect(() => {
    if (open) {
      setSearch('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        filteredCommands[selectedIndex].action();
        onClose();
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  }, [filteredCommands, selectedIndex, onClose]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const selectedEl = listRef.current.querySelector(`[data-index="${selectedIndex}"]`);
    if (selectedEl) {
      selectedEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [selectedIndex]);

  // Pre-compute flat index map for O(1) lookup
  const indexMap = useMemo(() => {
    const map = new Map<string, number>();
    filteredCommands.forEach((cmd, idx) => map.set(cmd.id, idx));
    return map;
  }, [filteredCommands]);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Navigate': return <SearchOutlined />;
      case 'Create': return <PlusOutlined />;
      case 'Actions': return <ThunderboltOutlined />;
      default: return <FireOutlined />;
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[1000] flex items-start justify-center pt-[15vh]"
          style={{ background: 'var(--ae-overlay)' }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -8 }}
            transition={{ duration: 0.2, ease: [0.25, 1, 0.5, 1] }}
            className="w-full max-w-[640px] mx-4 overflow-hidden"
            style={{
              background: 'var(--ae-panel-strong)',
              borderRadius: 12,
              boxShadow: 'var(--ae-shadow-ambient-high)',
              border: '1px solid var(--ae-line)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search Input */}
            <div
              className="flex items-center gap-3 px-4"
              style={{
                borderBottom: '1px solid var(--ae-line)',
                height: 56,
              }}
            >
              <SearchOutlined style={{ color: 'var(--ae-muted)', fontSize: 18 }} />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search commands..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setSelectedIndex(0); }}
                onKeyDown={handleKeyDown}
                className="flex-1 bg-transparent outline-none text-sm"
                style={{
                  color: 'var(--ae-text)',
                  fontFamily: 'var(--ae-font-family)',
                  fontSize: 15,
                }}
              />
              <kbd
                className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium rounded"
                style={{
                  background: 'rgba(255,255,255,0.5)',
                  color: 'var(--ae-muted)',
                  border: '1px solid var(--ae-line)',
                  fontFamily: 'var(--ae-font-family-mono)',
                }}
              >
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div
              ref={listRef}
              className="max-h-[420px] overflow-y-auto py-2"
            >
              {filteredCommands.length === 0 ? (
                <div
                  className="flex flex-col items-center justify-center py-12"
                  style={{ color: 'var(--ae-muted)' }}
                >
                  <SearchOutlined style={{ fontSize: 32, marginBottom: 12, opacity: 0.5 }} />
                  <Text style={{ fontSize: 14, color: 'var(--ae-muted)' }}>
                    No commands found for "{search}"
                  </Text>
                </div>
              ) : (
                Object.entries(groupedCommands).map(([category, cmds]) => {
                  const startIndex = indexMap.get(cmds[0].id) ?? 0;
                  return (
                    <div key={category}>
                      <div
                        className="flex items-center gap-2 px-4 py-1.5 text-xs font-medium uppercase tracking-wider"
                        style={{ color: 'var(--ae-muted)', letterSpacing: '0.06em' }}
                      >
                        {getCategoryIcon(category)}
                        {category}
                      </div>
                      {cmds.map((cmd) => {
                        const index = indexMap.get(cmd.id) ?? 0;
                        const isSelected = index === selectedIndex;
                        return (
                          <div
                            key={cmd.id}
                            data-index={index}
                            onClick={() => { cmd.action(); onClose(); }}
                            onMouseEnter={() => setSelectedIndex(index)}
                            className="flex items-center justify-between mx-2 px-3 py-2.5 rounded-md cursor-pointer transition-colors"
                            style={{
                              background: isSelected ? 'rgba(255,255,255,0.5)' : 'transparent',
                            }}
                          >
                            <div className="flex items-center gap-3">
                              <span
                                style={{
                                  color: isSelected ? 'var(--ae-accent-gold)' : 'var(--ae-muted)',
                                  fontSize: 16,
                                  transition: 'color 150ms cubic-bezier(0.25, 1, 0.5, 1)',
                                }}
                              >
                                {cmd.icon}
                              </span>
                              <div>
                                <div
                                  className="text-sm font-medium"
                                  style={{ color: 'var(--ae-text)' }}
                                >
                                  {cmd.label}
                                </div>
                                {cmd.description && (
                                  <div
                                    className="text-xs"
                                    style={{ color: 'var(--ae-muted)' }}
                                  >
                                    {cmd.description}
                                  </div>
                                )}
                              </div>
                            </div>
                            {cmd.shortcut && (
                              <kbd
                                className="text-xs px-1.5 py-0.5 rounded"
                                style={{
                                  background: 'rgba(255,255,255,0.5)',
                                  color: 'var(--ae-muted)',
                                  border: '1px solid var(--ae-line)',
                                  fontFamily: 'var(--ae-font-family-mono)',
                                }}
                              >
                                {cmd.shortcut}
                              </kbd>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div
              className="flex items-center justify-between px-4 py-2 text-xs"
              style={{
                borderTop: '1px solid var(--ae-line)',
                color: 'var(--ae-muted)',
              }}
            >
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: 'rgba(255,255,255,0.5)', border: '1px solid var(--ae-line)', fontFamily: 'var(--ae-font-family-mono)' }}>↑↓</kbd>
                  Navigate
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: 'rgba(255,255,255,0.5)', border: '1px solid var(--ae-line)', fontFamily: 'var(--ae-font-family-mono)' }}>↵</kbd>
                  Select
                </span>
              </div>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: 'rgba(255,255,255,0.5)', border: '1px solid var(--ae-line)', fontFamily: 'var(--ae-font-family-mono)' }}>ESC</kbd>
                Close
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
