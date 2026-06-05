import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConfirmModal from '../ConfirmModal';

describe('ConfirmModal', () => {
  const defaultProps = {
    open: true,
    title: 'Confirm Action',
    content: 'Are you sure?',
    onConfirm: jest.fn(),
    onCancel: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when open is true', () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('does not render content when open is false', () => {
    render(<ConfirmModal {...defaultProps} open={false} />);
    expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
  });

  it('renders default OK and Cancel button text', () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByText('OK')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('renders custom button text', () => {
    render(<ConfirmModal {...defaultProps} okText="Yes, Delete" cancelText="No, Keep" />);
    expect(screen.getByText('Yes, Delete')).toBeInTheDocument();
    expect(screen.getByText('No, Keep')).toBeInTheDocument();
  });

  it('calls onConfirm when OK button is clicked', async () => {
    render(<ConfirmModal {...defaultProps} />);
    fireEvent.click(screen.getByText('OK'));
    await waitFor(() => {
      expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    });
  });

  it('calls onCancel when Cancel button is clicked', async () => {
    render(<ConfirmModal {...defaultProps} />);
    fireEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
    });
  });

  it('renders React node as content', () => {
    render(
      <ConfirmModal
        {...defaultProps}
        content={<span data-testid="rich-content">Custom <strong>content</strong></span>}
      />
    );
    expect(screen.getByTestId('rich-content')).toBeInTheDocument();
  });

  it('applies danger background to OK button when danger is true', () => {
    render(<ConfirmModal {...defaultProps} danger={true} />);
    const okButton = screen.getByText('OK').closest('button');
    expect(okButton?.style.background).toContain('var(--ae-danger');
  });

  it('applies accent background by default', () => {
    render(<ConfirmModal {...defaultProps} />);
    const okButton = screen.getByText('OK').closest('button');
    expect(okButton?.style.background).toContain('var(--ae-accent');
  });

  it('shows loading state when confirmLoading is true', () => {
    render(<ConfirmModal {...defaultProps} confirmLoading={true} />);
    const okButton = screen.getByText('…').closest('button');
    expect(okButton).toBeDisabled();
  });

  it('disables cancel button during loading', () => {
    render(<ConfirmModal {...defaultProps} confirmLoading={true} />);
    const cancelButton = screen.getByText('Cancel').closest('button');
    expect(cancelButton).toBeDisabled();
  });

  it('has dialog role with aria-modal', () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  it('has aria-label matching title', () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-label', 'Confirm Action');
  });

  it('calls onCancel when overlay is clicked', () => {
    render(<ConfirmModal {...defaultProps} />);
    fireEvent.click(screen.getByRole('dialog'));
    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel on Escape key', () => {
    render(<ConfirmModal {...defaultProps} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });
});
