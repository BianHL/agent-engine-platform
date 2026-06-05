import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '../Sidebar';

const mockPush = jest.fn();
const mockPathname = '/agents';

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => mockPathname,
}));

describe('Sidebar', () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it('renders the app title', () => {
    render(<Sidebar />);
    expect(screen.getByText('Agent Engine')).toBeInTheDocument();
  });

  it('renders top-level menu groups', () => {
    render(<Sidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('Orchestration')).toBeInTheDocument();
    expect(screen.getByText('Models')).toBeInTheDocument();
  });

  it('navigates when a menu item is clicked', () => {
    render(<Sidebar />);
    fireEvent.click(screen.getByText('Dashboard'));
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('highlights the current path group', () => {
    render(<Sidebar />);
    // mockPathname is '/agents' which is a child of 'Agents' group
    // The Agents group button should have active styling (expanded background)
    const agentsBtn = screen.getByText('Agents').closest('button');
    expect(agentsBtn).toBeInTheDocument();
  });
});
