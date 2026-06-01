'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { ConfigProvider, theme as antdTheme } from 'antd';
import { defaultTheme, darkTheme, applyCssVariables, type ThemeMode } from '@/lib/theme';

interface ThemeContextValue {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

function getInitialMode(): ThemeMode {
  if (typeof window === 'undefined') return 'light';
  const stored = localStorage.getItem('ae-theme') as ThemeMode | null;
  if (stored === 'dark' || stored === 'light') return stored;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return prefersDark ? 'dark' : 'light';
}

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => getInitialMode());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    applyCssVariables(mode);
    setMounted(true);
  }, [mode]);

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    applyCssVariables(newMode);
    localStorage.setItem('ae-theme', newMode);
  }, []);

  const toggleMode = useCallback(() => {
    setMode(mode === 'light' ? 'dark' : 'light');
  }, [mode]);

  const antdThemeConfig = mode === 'dark' ? darkTheme : defaultTheme;

  // During SSR/hydration, render with the initial mode to avoid mismatch
  // The first client-side effect will apply the correct CSS variables
  return (
    <ThemeContext.Provider value={{ mode, setMode, toggleMode }}>
      <ConfigProvider
        theme={{
          ...antdThemeConfig,
          algorithm: mode === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        }}
      >
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
}
