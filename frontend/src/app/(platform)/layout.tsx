'use client';
import React, { useEffect, useState, useCallback } from 'react';
import { Layout } from 'antd';
import {
  DashboardOutlined, RobotOutlined, DatabaseOutlined,
  BranchesOutlined, ToolOutlined,
} from '@ant-design/icons';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ErrorBoundary from '@/components/ErrorBoundary';
import CommandPalette from '@/components/CommandPalette';
import { OnboardingProvider, type OnboardingStep } from '@/components/onboarding';
import BreadcrumbNav from '@/components/BreadcrumbNav';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';

const { Content } = Layout;

const onboardingSteps: OnboardingStep[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    description: 'Get an overview of your platform activity. Monitor token usage, costs, agent performance, and user feedback all in one place.',
    targetSelector: '[data-menu-id="/dashboard"]',
    route: '/dashboard',
    icon: <DashboardOutlined />,
  },
  {
    id: 'agents',
    title: 'Agents',
    description: 'Create and manage AI agents powered by large language models. Each agent can have its own persona, tools, and knowledge base.',
    targetSelector: '[data-menu-id="/agents"]',
    route: '/agents',
    icon: <RobotOutlined />,
  },
  {
    id: 'knowledge',
    title: 'Knowledge Base',
    description: 'Upload documents to ground your agents with domain-specific knowledge. Supports PDF, Word, and text files with automatic chunking and embedding.',
    targetSelector: '[data-menu-id="/knowledge"]',
    route: '/knowledge',
    icon: <DatabaseOutlined />,
  },
  {
    id: 'workflows',
    title: 'Workflows',
    description: 'Build multi-step automated processes using a visual DAG editor. Chain LLM calls, conditions, loops, and human approvals together.',
    targetSelector: '[data-menu-id="/workflows"]',
    route: '/workflows',
    icon: <BranchesOutlined />,
  },
  {
    id: 'tools',
    title: 'Tools',
    description: 'Configure external tools and APIs that your agents can invoke. Register custom tools or use built-in ones to extend agent capabilities.',
    targetSelector: '[data-menu-id="/tools"]',
    route: '/tools',
    icon: <ToolOutlined />,
  },
];

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, checkAuth } = useAuthStore();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  useEffect(() => {
    if (!token) {
      const currentPath = window.location.pathname;
      if (currentPath !== '/login') {
        router.push('/login');
      }
    } else {
      checkAuth();
    }
  }, [token, checkAuth, router]);

  // Global keyboard shortcut for Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const openCommandPalette = useCallback(() => setCommandPaletteOpen(true), []);
  const closeCommandPalette = useCallback(() => setCommandPaletteOpen(false), []);

  if (!token) return null;

  return (
    <OnboardingProvider steps={onboardingSteps}>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[1001] focus:px-4 focus:py-2 focus:rounded-md focus:bg-[var(--ae-accent-olive)] focus:text-white focus:font-medium"
      >
        Skip to main content
      </a>
      <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
        <Sidebar
          mobileOpen={mobileSidebarOpen}
          onMobileClose={() => setMobileSidebarOpen(false)}
        />
        <Layout
          style={{
            background: 'transparent',
          }}
          className="md:ml-[280px]"
        >
          <Header
            onMenuClick={() => setMobileSidebarOpen(true)}
            onSearchClick={openCommandPalette}
          />
          <Content
            style={{
              padding: 'var(--ae-content-padding)',
              background: 'transparent',
              minHeight: 'calc(100vh - 64px)',
            }}
          >
            <div
              id="main-content"
              style={{
                background: 'var(--ae-panel)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                borderRadius: 'var(--ae-radius-xl)',
                border: '1px solid var(--ae-line)',
                boxShadow: 'var(--ae-shadow-soft)',
                minHeight: 'calc(100vh - 64px - 2 * var(--ae-content-padding))',
                padding: 'var(--ae-content-padding)',
              }}
              className="animate-float-in"
            >
              <BreadcrumbNav />
              <ErrorBoundary>
                {children}
              </ErrorBoundary>
            </div>
          </Content>
        </Layout>
      </Layout>

      <CommandPalette open={commandPaletteOpen} onClose={closeCommandPalette} />
    </OnboardingProvider>
  );
}
