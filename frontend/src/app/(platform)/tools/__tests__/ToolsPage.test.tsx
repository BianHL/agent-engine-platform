import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ToolsPage from '../page';

// Mock the API module
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    listBuiltinTools: jest.fn(),
    listTools: jest.fn(),
    getToolExecutions: jest.fn(),
    createTool: jest.fn(),
    deleteTool: jest.fn(),
    executeTool: jest.fn(),
  },
}));

// Mock antd message
jest.mock('antd', () => {
  const antd = jest.requireActual('antd');
  return {
    ...antd,
    message: {
      success: jest.fn(),
      error: jest.fn(),
    },
  };
});

import api from '@/lib/api';

const mockedApi = api as jest.Mocked<typeof api>;

describe('ToolsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the tools page title', async () => {
    mockedApi.listBuiltinTools.mockResolvedValue([]);
    mockedApi.listTools.mockResolvedValue([]);
    mockedApi.getToolExecutions.mockResolvedValue([]);

    render(<ToolsPage />);

    expect(screen.getByText('Tools')).toBeInTheDocument();
  });

  it('renders the builtin tools table with data', async () => {
    const builtinTools = [
      { name: 'web_search', description: 'Search the web', input_schema: { properties: {} } },
      { name: 'calculator', description: 'Calculate expressions', input_schema: { properties: {} } },
    ];

    mockedApi.listBuiltinTools.mockResolvedValue(builtinTools);
    mockedApi.listTools.mockResolvedValue([]);
    mockedApi.getToolExecutions.mockResolvedValue([]);

    render(<ToolsPage />);

    await waitFor(() => {
      expect(screen.getByText('web_search')).toBeInTheDocument();
    });

    expect(screen.getByText('calculator')).toBeInTheDocument();
    expect(screen.getByText('Search the web')).toBeInTheDocument();
  });

  it('renders tab labels with counts', async () => {
    const builtinTools = [
      { name: 'tool1', description: 'Tool 1', input_schema: { properties: {} } },
    ];
    const allTools = [
      { id: '1', name: 'custom1', description: 'Custom 1', tool_type: 'custom', enabled: true },
    ];
    const executions = [
      { id: '1', tool_name: 'tool1', status: 'success', duration_ms: 100, created_at: '2024-01-01' },
    ];

    mockedApi.listBuiltinTools.mockResolvedValue(builtinTools);
    mockedApi.listTools.mockResolvedValue(allTools);
    mockedApi.getToolExecutions.mockResolvedValue(executions);

    render(<ToolsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Built-in \(1\)/)).toBeInTheDocument();
    });

    expect(screen.getByText(/Custom \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/Execution History \(1\)/)).toBeInTheDocument();
  });

  it('shows empty state for custom tools when none exist', async () => {
    mockedApi.listBuiltinTools.mockResolvedValue([]);
    mockedApi.listTools.mockResolvedValue([]);
    mockedApi.getToolExecutions.mockResolvedValue([]);

    render(<ToolsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Custom \(0\)/)).toBeInTheDocument();
    });
  });

  it('renders the Create Custom Tool button', async () => {
    mockedApi.listBuiltinTools.mockResolvedValue([]);
    mockedApi.listTools.mockResolvedValue([]);
    mockedApi.getToolExecutions.mockResolvedValue([]);

    render(<ToolsPage />);

    expect(screen.getByText('Create Custom Tool')).toBeInTheDocument();
  });
});
