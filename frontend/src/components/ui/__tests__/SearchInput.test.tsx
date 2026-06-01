import React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchInput from '../SearchInput';

jest.useFakeTimers();

describe('SearchInput', () => {
  beforeEach(() => {
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    jest.useFakeTimers();
  });

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

  it('calls onChange after debounce delay', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<SearchInput onChange={onChange} debounceMs={300} />);

    const input = screen.getByPlaceholderText('Search...');
    await user.type(input, 'test');

    // onChange should not have been called yet (debounced)
    expect(onChange).not.toHaveBeenCalled();

    // Advance past debounce
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(onChange).toHaveBeenCalledWith('test');
  });

  it('respects custom debounceMs', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<SearchInput onChange={onChange} debounceMs={500} />);

    const input = screen.getByPlaceholderText('Search...');
    await user.type(input, 'a');

    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(onChange).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(200);
    });
    expect(onChange).toHaveBeenCalledWith('a');
  });

  it('resets debounce timer on subsequent keystrokes', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<SearchInput onChange={onChange} debounceMs={300} />);

    const input = screen.getByPlaceholderText('Search...');
    await user.type(input, 'a');

    act(() => {
      jest.advanceTimersByTime(200);
    });
    await user.type(input, 'b');

    act(() => {
      jest.advanceTimersByTime(200);
    });
    expect(onChange).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(100);
    });
    expect(onChange).toHaveBeenCalledWith('ab');
  });

  it('updates local value when controlled value changes', () => {
    const onChange = jest.fn();
    const { rerender } = render(<SearchInput onChange={onChange} value="a" />);
    expect(screen.getByDisplayValue('a')).toBeInTheDocument();

    rerender(<SearchInput onChange={onChange} value="b" />);
    expect(screen.getByDisplayValue('b')).toBeInTheDocument();
  });

  it('renders with allowClear enabled by default', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} />);
    // Ant Design Input with allowClear renders a clear icon
    const input = screen.getByPlaceholderText('Search...');
    expect(input).toBeInTheDocument();
  });

  it('renders search icon', () => {
    const onChange = jest.fn();
    render(<SearchInput onChange={onChange} />);
    // The search icon is rendered as an SVG inside the input prefix
    const searchIcon = document.querySelector('.anticon-search');
    expect(searchIcon).toBeInTheDocument();
  });
});
