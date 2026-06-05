import React from 'react';
import { render, screen } from '@testing-library/react';
import StatusBadge from '../StatusBadge';

describe('StatusBadge', () => {
  it('renders with default text from status', () => {
    render(<StatusBadge status="success" />);
    expect(screen.getByText('Success')).toBeInTheDocument();
  });

  it('renders with custom text', () => {
    render(<StatusBadge status="danger" text="Critical" />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('renders all status types', () => {
    const statuses = ['success', 'warning', 'danger', 'info', 'processing'] as const;
    statuses.forEach((status) => {
      const { unmount } = render(<StatusBadge status={status} />);
      expect(screen.getByText(status.charAt(0).toUpperCase() + status.slice(1))).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with sm size', () => {
    render(<StatusBadge status="info" size="sm" />);
    expect(screen.getByText('Info')).toBeInTheDocument();
  });

  it('has accessible aria-label on dot', () => {
    render(<StatusBadge status="success" />);
    expect(screen.getByLabelText('Status: Success')).toBeInTheDocument();
  });

  it('applies pulse class for processing status', () => {
    render(<StatusBadge status="processing" />);
    const dot = screen.getByLabelText('Status: Processing');
    expect(dot.className).toContain('status-pulse');
  });

  it('does not apply pulse class for non-processing status', () => {
    render(<StatusBadge status="success" />);
    const dot = screen.getByLabelText('Status: Success');
    expect(dot.className).not.toContain('status-pulse');
  });
});
