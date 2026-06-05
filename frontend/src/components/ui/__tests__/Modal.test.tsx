import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Modal from '../Modal';

describe('Modal', () => {
  const defaultProps = {
    open: true,
    title: 'Test Modal',
    onClose: jest.fn(),
    children: <div>Modal content</div>,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders when open is true', () => {
      render(<Modal {...defaultProps} />);
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
      expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      render(<Modal {...defaultProps} open={false} />);
      expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
    });

    it('renders footer when provided', () => {
      render(
        <Modal {...defaultProps} footer={<button>Save</button>}>
          Content
        </Modal>
      );
      expect(screen.getByText('Save')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role=dialog', () => {
      render(<Modal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has aria-modal=true', () => {
      render(<Modal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('has aria-labelledby pointing to title', () => {
      render(<Modal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      const titleId = dialog.getAttribute('aria-labelledby');
      expect(titleId).toBeTruthy();
      expect(document.getElementById(titleId!)).toHaveTextContent('Test Modal');
    });

    it('has close button with aria-label', () => {
      render(<Modal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });
  });

  describe('Close Actions', () => {
    it('calls onClose when close button is clicked', () => {
      const onClose = jest.fn();
      render(<Modal {...defaultProps} onClose={onClose} />);
      fireEvent.click(screen.getByRole('button', { name: /close/i }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when overlay is clicked by default', () => {
      const onClose = jest.fn();
      render(<Modal {...defaultProps} onClose={onClose} />);
      const overlay = document.querySelector('.modal-overlay')!;
      fireEvent.click(overlay);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('does not call onClose when maskClosable is false and overlay is clicked', () => {
      const onClose = jest.fn();
      render(<Modal {...defaultProps} onClose={onClose} maskClosable={false} />);
      const overlay = document.querySelector('.modal-overlay')!;
      fireEvent.click(overlay);
      expect(onClose).not.toHaveBeenCalled();
    });

    it('calls onClose on Escape key', () => {
      const onClose = jest.fn();
      render(<Modal {...defaultProps} onClose={onClose} />);
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Size Variants', () => {
    it('uses default maxWidth for sm size', () => {
      render(<Modal {...defaultProps} size="sm" />);
      const content = document.querySelector('.modal-content') as HTMLElement;
      expect(content.style.maxWidth).toBe('400px');
    });

    it('uses default maxWidth for md size (default)', () => {
      render(<Modal {...defaultProps} />);
      const content = document.querySelector('.modal-content') as HTMLElement;
      expect(content.style.maxWidth).toBe('480px');
    });

    it('uses larger maxWidth for lg size', () => {
      render(<Modal {...defaultProps} size="lg" />);
      const content = document.querySelector('.modal-content') as HTMLElement;
      expect(content.style.maxWidth).toBe('640px');
    });

    it('uses largest maxWidth for xl size', () => {
      render(<Modal {...defaultProps} size="xl" />);
      const content = document.querySelector('.modal-content') as HTMLElement;
      expect(content.style.maxWidth).toBe('800px');
    });
  });
});
