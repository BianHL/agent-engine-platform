import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Alert from '../Alert';

describe('Alert', () => {
  describe('Rendering', () => {
    it('renders message text', () => {
      render(<Alert message="Test alert" />);
      expect(screen.getByText('Test alert')).toBeInTheDocument();
    });

    it('renders description when provided', () => {
      render(<Alert message="Title" description="Details here" />);
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Details here')).toBeInTheDocument();
    });

    it('renders with default type (info)', () => {
      render(<Alert message="Info" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Type Variants', () => {
    it('renders info type', () => {
      render(<Alert type="info" message="Info alert" />);
      expect(screen.getByText('ℹ')).toBeInTheDocument();
    });

    it('renders success type', () => {
      render(<Alert type="success" message="Success alert" />);
      expect(screen.getByText('✓')).toBeInTheDocument();
    });

    it('renders warning type', () => {
      render(<Alert type="warning" message="Warning alert" />);
      expect(screen.getByText('!')).toBeInTheDocument();
    });

    it('renders error type', () => {
      render(<Alert type="error" message="Error alert" />);
      const elements = screen.getAllByText('✕');
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Close Behavior', () => {
    it('shows close button by default', () => {
      render(<Alert message="Closable" />);
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });

    it('hides alert when close is clicked', () => {
      render(<Alert message="Gone" />);
      fireEvent.click(screen.getByRole('button', { name: /close/i }));
      expect(screen.queryByText('Gone')).not.toBeInTheDocument();
    });

    it('calls onClose callback when closed', () => {
      const onClose = jest.fn();
      render(<Alert message="Callback" onClose={onClose} />);
      fireEvent.click(screen.getByRole('button', { name: /close/i }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('hides close button when closable is false', () => {
      render(<Alert message="Persistent" closable={false} />);
      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument();
    });
  });

  describe('Icon', () => {
    it('shows icon by default', () => {
      render(<Alert message="With icon" />);
      expect(screen.getByText('ℹ')).toBeInTheDocument();
    });

    it('hides icon when showIcon is false', () => {
      render(<Alert message="No icon" showIcon={false} />);
      expect(screen.queryByText('ℹ')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role=alert', () => {
      render(<Alert message="Alert" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('close button has aria-label', () => {
      render(<Alert message="Test" />);
      expect(screen.getByRole('button', { name: /close alert/i })).toBeInTheDocument();
    });
  });
});
