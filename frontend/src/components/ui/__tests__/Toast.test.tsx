import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { ToastContainer, showToast, toast } from '../Toast';

describe('Toast', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders ToastContainer', () => {
    render(<ToastContainer />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has accessible aria attributes', () => {
    render(<ToastContainer />);
    const container = screen.getByRole('status');
    expect(container).toHaveAttribute('aria-live', 'polite');
    expect(container).toHaveAttribute('aria-atomic', 'true');
  });

  it('shows a success toast', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Saved successfully', 'success');
    });
    expect(screen.getByText('Saved successfully')).toBeInTheDocument();
  });

  it('shows an error toast', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Something failed', 'error');
    });
    expect(screen.getByText('Something failed')).toBeInTheDocument();
  });

  it('shows a warning toast', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Check this', 'warning');
    });
    expect(screen.getByText('Check this')).toBeInTheDocument();
  });

  it('toast.show is an alias for showToast', () => {
    render(<ToastContainer />);
    act(() => {
      toast.show('Via alias');
    });
    expect(screen.getByText('Via alias')).toBeInTheDocument();
  });

  it('auto-dismisses success toast after 3s', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Gone soon', 'success');
    });
    expect(screen.getByText('Gone soon')).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(3000);
    });
    expect(screen.queryByText('Gone soon')).not.toBeInTheDocument();
  });

  it('auto-dismisses error toast after 5s', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Error stays longer', 'error');
    });
    expect(screen.getByText('Error stays longer')).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(4999);
    });
    expect(screen.getByText('Error stays longer')).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(screen.queryByText('Error stays longer')).not.toBeInTheDocument();
  });

  it('shows multiple toasts', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('First', 'success');
      showToast('Second', 'error');
    });
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });
});
