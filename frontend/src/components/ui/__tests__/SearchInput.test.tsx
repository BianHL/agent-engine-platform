import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SearchInput from '../SearchInput';

describe('SearchInput', () => {
  it('renders with default placeholder', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} />);
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
  });

  it('renders with custom placeholder', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} placeholder="Find items..." />);
    expect(screen.getByPlaceholderText('Find items...')).toBeInTheDocument();
  });

  it('displays controlled value', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} value="initial" />);
    expect(screen.getByDisplayValue('initial')).toBeInTheDocument();
  });

  it('calls onChange on input change', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} />);
    const input = screen.getByPlaceholderText('Search...');
    fireEvent.change(input, { target: { value: 'test' } });
    expect(onChange).toHaveBeenCalledWith('test');
  });

  it('updates local value when controlled value changes', () => {
    const onChange = jest.fn();
    const { rerender } = render(<SearchInput onChange={onChange} value="a" />);
    expect(screen.getByDisplayValue('a')).toBeInTheDocument();

    rerender(<SearchInput onChange={onChange} value="b" />);
    expect(screen.getByDisplayValue('b')).toBeInTheDocument();
  });

  it('renders search icon', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} />);
    const searchIcon = document.querySelector('.anticon-search');
    expect(searchIcon).toBeInTheDocument();
  });
});
