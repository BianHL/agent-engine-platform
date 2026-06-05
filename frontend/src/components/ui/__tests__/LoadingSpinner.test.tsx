import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders a spinner by default', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders with default large size (36px)', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner.style.width).toBe('36px');
    expect(spinner.style.height).toBe('36px');
  });

  it('renders with small size (16px)', () => {
    render(<LoadingSpinner size="small" />);
    const spinner = screen.getByRole('status');
    expect(spinner.style.width).toBe('16px');
    expect(spinner.style.height).toBe('16px');
  });

  it('renders with default size (24px)', () => {
    render(<LoadingSpinner size="default" />);
    const spinner = screen.getByRole('status');
    expect(spinner.style.width).toBe('24px');
    expect(spinner.style.height).toBe('24px');
  });

  it('renders tip text when provided', () => {
    render(<LoadingSpinner tip="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('sets aria-label from tip', () => {
    render(<LoadingSpinner tip="Loading data..." />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading data...');
  });

  it('sets default aria-label when no tip', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading');
  });

  it('applies fullScreen styles when fullScreen is true', () => {
    const { container } = render(<LoadingSpinner fullScreen />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.style.height).toBe('100%');
    expect(wrapper.style.minHeight).toBe('200px');
  });

  it('applies default padding when fullScreen is false', () => {
    const { container } = render(<LoadingSpinner />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.style.padding).toBe('40px 0px');
  });

  it('has spinner animation', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner.style.animation).toContain('ae-spin');
  });
});
