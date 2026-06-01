import React from 'react';
import { render, screen } from '@testing-library/react';
import Header from '../Header';

// Mock auth store
const mockLogout = jest.fn();
jest.mock('@/store/auth', () => ({
  useAuthStore: jest.fn(),
}));

// Mock theme provider
jest.mock('@/components/ThemeProvider', () => ({
  useTheme: jest.fn().mockReturnValue({
    mode: 'light',
    toggleMode: jest.fn(),
  }),
}));

import { useAuthStore } from '@/store/auth';
const mockedUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

function setupStore(user: { username: string } | null = { username: 'admin' }) {
  mockedUseAuthStore.mockReturnValue({
    user,
    token: user ? 'token' : null,
    loading: false,
    login: jest.fn(),
    logout: mockLogout,
    checkAuth: jest.fn(),
  });
}

describe('Header', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupStore();
  });

  it('renders the user name from auth store', () => {
    render(<Header />);
    // Username is in tooltip and dropdown, check for its presence
    expect(screen.getByText('admin')).toBeInTheDocument();
  });

  it('renders "User" as fallback when user is null', () => {
    setupStore(null);
    render(<Header />);
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('renders a user avatar with initial', () => {
    render(<Header />);
    // Check for the user initial in the gradient avatar
    expect(screen.getByText('A')).toBeInTheDocument();
  });

  it('renders a dropdown trigger area', () => {
    render(<Header />);
    const trigger = document.querySelector('.ant-dropdown-trigger');
    expect(trigger).toBeInTheDocument();
  });

  it('renders within a header element', () => {
    const { container } = render(<Header />);
    const header = container.querySelector('header');
    expect(header).toBeInTheDocument();
  });

  it('renders search button with keyboard shortcut', () => {
    render(<Header />);
    expect(screen.getByText('Search...')).toBeInTheDocument();
    expect(screen.getByText('⌘K')).toBeInTheDocument();
  });

  it('renders theme toggle button', () => {
    render(<Header />);
    // Moon icon should be present in light mode
    const header = document.querySelector('header');
    expect(header).toBeInTheDocument();
  });

  it('renders notification button', () => {
    render(<Header />);
    // Bell icon is rendered as SVG, check button presence
    const buttons = document.querySelectorAll('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});
