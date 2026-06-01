import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import EmptyState from '../EmptyState';

describe('EmptyState', () => {
  it('renders description text', () => {
    render(<EmptyState description="No data found" />);
    expect(screen.getByText('No data found')).toBeInTheDocument();
  });

  it('renders Ant Design Empty component', () => {
    const { container } = render(<EmptyState description="Empty" />);
    expect(container.querySelector('.ant-empty')).toBeInTheDocument();
  });

  it('does not render action button when actionLabel is not provided', () => {
    render(<EmptyState description="No items" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('does not render action button when onAction is not provided', () => {
    render(<EmptyState description="No items" actionLabel="Create" />);
    expect(screen.queryByRole('button', { name: 'Create' })).not.toBeInTheDocument();
  });

  it('renders action button when both actionLabel and onAction are provided', () => {
    const onAction = jest.fn();
    render(<EmptyState description="No items" actionLabel="Create New" onAction={onAction} />);
    expect(screen.getByText('Create New')).toBeInTheDocument();
  });

  it('calls onAction when action button is clicked', () => {
    const onAction = jest.fn();
    render(<EmptyState description="No items" actionLabel="Add Item" onAction={onAction} />);
    fireEvent.click(screen.getByText('Add Item'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('renders custom icon when provided', () => {
    render(
      <EmptyState
        description="No results"
        icon={<span data-testid="custom-icon">icon</span>}
      />
    );
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  it('renders default Ant Design empty image when icon is not provided', () => {
    const { container } = render(<EmptyState description="Nothing here" />);
    // Ant Design Empty renders an image element by default
    const emptyImage = container.querySelector('.ant-empty-image');
    expect(emptyImage).toBeInTheDocument();
  });
});
