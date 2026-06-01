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

  it('renders all menu items', () => {
    render(<Sidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Workflows')).toBeInTheDocument();
    expect(screen.getByText('Models')).toBeInTheDocument();
    expect(screen.getByText('Tools')).toBeInTheDocument();
    expect(screen.getByText('Conversations')).toBeInTheDocument();
    expect(screen.getByText('Audit Logs')).toBeInTheDocument();
  });

  it('navigates when a menu item is clicked', () => {
    render(<Sidebar />);
    fireEvent.click(screen.getByText('Dashboard'));
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('highlights the current path', () => {
    render(<Sidebar />);
    // The agents menu item should be selected based on mockPathname
    const agentsItem = screen.getByText('Agents').closest('.ant-menu-item');
    expect(agentsItem).toHaveClass('ant-menu-item-selected');
  });
});
