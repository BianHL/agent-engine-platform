'use client';
import { create } from 'zustand';

interface LoadingState {
  globalLoading: boolean;
  loadingStates: Record<string, boolean>;
  loadingMessages: Record<string, string>;

  // Actions
  setGlobalLoading: (loading: boolean, message?: string) => void;
  setLoading: (key: string, loading: boolean, message?: string) => void;
  isLoading: (key: string) => boolean;
  getLoadingMessage: (key: string) => string;
  clearAll: () => void;
  withLoading: <T>(key: string, fn: () => Promise<T>, message?: string) => Promise<T>;
}

export const useLoadingStore = create<LoadingState>((set, get) => ({
  globalLoading: false,
  loadingStates: {},
  loadingMessages: {},

  setGlobalLoading: (loading: boolean, message?: string) => {
    set({
      globalLoading: loading,
      ...(message ? { loadingMessages: { ...get().loadingMessages, global: message } } : {}),
    });
  },

  setLoading: (key: string, loading: boolean, message?: string) => {
    set((state) => ({
      loadingStates: { ...state.loadingStates, [key]: loading },
      ...(message ? { loadingMessages: { ...state.loadingMessages, [key]: message } } : {}),
    }));
  },

  isLoading: (key: string) => {
    return get().loadingStates[key] ?? false;
  },

  getLoadingMessage: (key: string) => {
    return get().loadingMessages[key] ?? '';
  },

  clearAll: () => {
    set({ globalLoading: false, loadingStates: {}, loadingMessages: {} });
  },

  withLoading: async <T>(key: string, fn: () => Promise<T>, message?: string): Promise<T> => {
    const { setLoading } = get();
    setLoading(key, true, message);
    try {
      return await fn();
    } finally {
      setLoading(key, false);
    }
  },
}));

// Hook for single loading state
export function useLoading(key: string) {
  const { isLoading, setLoading, getLoadingMessage } = useLoadingStore();

  return {
    loading: isLoading(key),
    message: getLoadingMessage(key),
    startLoading: (message?: string) => setLoading(key, true, message),
    stopLoading: () => setLoading(key, false),
  };
}

// Hook for async operations with loading state
export function useAsyncOperation(key: string) {
  const { setLoading, isLoading } = useLoadingStore();

  const execute = async <T>(
    fn: () => Promise<T>,
    options?: {
      loadingMessage?: string;
      onSuccess?: (result: T) => void;
      onError?: (error: Error) => void;
    }
  ): Promise<T | null> => {
    setLoading(key, true, options?.loadingMessage);
    try {
      const result = await fn();
      options?.onSuccess?.(result);
      return result;
    } catch (error) {
      options?.onError?.(error instanceof Error ? error : new Error(String(error)));
      return null;
    } finally {
      setLoading(key, false);
    }
  };

  return {
    loading: isLoading(key),
    execute,
  };
}

// Common loading keys
export const LOADING_KEYS = {
  AUTH: 'auth',
  AGENTS: 'agents',
  AGENT_DETAIL: 'agent-detail',
  KNOWLEDGE_BASES: 'knowledge-bases',
  KNOWLEDGE_DETAIL: 'knowledge-detail',
  WORKFLOWS: 'workflows',
  WORKFLOW_DETAIL: 'workflow-detail',
  TOOLS: 'tools',
  MODELS: 'models',
  CONVERSATIONS: 'conversations',
  CONVERSATION_MESSAGES: 'conversation-messages',
  AUDIT_LOGS: 'audit-logs',
  DASHBOARD: 'dashboard',
  MARKETPLACE: 'marketplace',
  USER_PROFILE: 'user-profile',
} as const;

// Loading middleware for API calls
export function withLoadingState<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  key: string,
  message?: string
): T {
  return (async (...args: Parameters<T>) => {
    const { setLoading } = useLoadingStore.getState();
    setLoading(key, true, message);
    try {
      return await fn(...args);
    } finally {
      setLoading(key, false);
    }
  }) as T;
}

// Debounced loading state (prevents flashing for quick operations)
export function useDebouncedLoading(key: string, delay: number = 300) {
  const [debouncedLoading, setDebouncedLoading] = useState(false);
  const { isLoading } = useLoadingStore();
  const loading = isLoading(key);

  useEffect(() => {
    if (loading) {
      // Show loading immediately
      setDebouncedLoading(true);
    } else {
      // Delay hiding loading
      const timer = setTimeout(() => setDebouncedLoading(false), delay);
      return () => clearTimeout(timer);
    }
  }, [loading, delay]);

  return debouncedLoading;
}

import { useState, useEffect } from 'react';

// Progress tracking for multi-step operations
interface ProgressState {
  current: number;
  total: number;
  percentage: number;
  message: string;
}

export function useProgress(key: string) {
  const [progress, setProgress] = useState<ProgressState>({
    current: 0,
    total: 0,
    percentage: 0,
    message: '',
  });

  const updateProgress = (current: number, total: number, message?: string) => {
    setProgress({
      current,
      total,
      percentage: total > 0 ? Math.round((current / total) * 100) : 0,
      message: message ?? '',
    });
  };

  const resetProgress = () => {
    setProgress({ current: 0, total: 0, percentage: 0, message: '' });
  };

  return { progress, updateProgress, resetProgress };
}
