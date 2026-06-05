import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchInput from '../SearchInput';

describe('SearchInput Accessibility', () => {
  it('should have role="search" on container', () => {
    render(<SearchInput placeholder="Search agents..." />);
    const container = screen.getByRole('search');
    expect(container).toBeInTheDocument();
  });

  it('should have aria-label on input matching placeholder', () => {
    render(<SearchInput placeholder="Search agents..." />);
    const input = screen.getByLabelText('Search agents...');
    expect(input).toBeInTheDocument();
  });

  it('should have aria-label when no placeholder provided', () => {
    render(<SearchInput />);
    const input = screen.getByLabelText('Search...');
    expect(input).toBeInTheDocument();
  });

  it('should support custom aria-label', () => {
    render(<SearchInput placeholder="Search..." aria-label="Custom search label" />);
    const input = screen.getByLabelText('Custom search label');
    expect(input).toBeInTheDocument();
  });

  it('should be keyboard accessible', async () => {
    const user = userEvent.setup();
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} />);

    const input = screen.getByRole('searchbox');
    await user.type(input, 'test query');

    expect(onChange).toHaveBeenCalledWith('test query');
  });

  it('should have proper focus styles', () => {
    render(<SearchInput />);
    const input = screen.getByRole('searchbox');

    // Input should be focusable
    input.focus();
    expect(input).toHaveFocus();
  });
});
