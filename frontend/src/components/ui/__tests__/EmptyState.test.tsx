import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import EmptyState from '../EmptyState';

describe('EmptyState', () => {
  it('renders title text', () => {
    render(<EmptyState title="No data found" />);
    expect(screen.getByText('No data found')).toBeInTheDocument();
  });

  it('renders description text when provided', () => {
    render(<EmptyState title="Empty" description="Try adding some items" />);
    expect(screen.getByText('Try adding some items')).toBeInTheDocument();
  });

  it('does not render action button when actionLabel is not provided', () => {
    render(<EmptyState title="No items" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('does not render action button when onAction is not provided', () => {
    render(<EmptyState title="No items" actionLabel="Create" />);
    expect(screen.queryByRole('button', { name: 'Create' })).not.toBeInTheDocument();
  });

  it('renders action button when both actionLabel and onAction are provided', () => {
    const onAction = jest.fn();
    render(<EmptyState title="No items" actionLabel="Create New" onAction={onAction} />);
    expect(screen.getByText('Create New')).toBeInTheDocument();
  });

  it('calls onAction when action button is clicked', () => {
    const onAction = jest.fn();
    render(<EmptyState title="No items" actionLabel="Add Item" onAction={onAction} />);
    fireEvent.click(screen.getByText('Add Item'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('renders custom icon when provided', () => {
    render(
      <EmptyState
        title="No results"
        icon={<span data-testid="custom-icon">icon</span>}
      />
    );
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });
});
