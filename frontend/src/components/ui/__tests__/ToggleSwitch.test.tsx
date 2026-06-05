import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ToggleSwitch from '../ToggleSwitch';

describe('ToggleSwitch', () => {
  it('renders with correct aria-checked when unchecked', () => {
    render(<ToggleSwitch checked={false} onChange={() => {}} />);
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('renders with correct aria-checked when checked', () => {
    render(<ToggleSwitch checked={true} onChange={() => {}} />);
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'true');
  });

  it('calls onChange with true when clicked while unchecked', () => {
    const onChange = jest.fn();
    render(<ToggleSwitch checked={false} onChange={onChange} />);
    fireEvent.click(screen.getByRole('switch'));
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('calls onChange with false when clicked while checked', () => {
    const onChange = jest.fn();
    render(<ToggleSwitch checked={true} onChange={onChange} />);
    fireEvent.click(screen.getByRole('switch'));
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('toggles on Space key', () => {
    const onChange = jest.fn();
    render(<ToggleSwitch checked={false} onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole('switch'), { key: ' ' });
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('toggles on Enter key', () => {
    const onChange = jest.fn();
    render(<ToggleSwitch checked={false} onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole('switch'), { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('does not toggle on other keys', () => {
    const onChange = jest.fn();
    render(<ToggleSwitch checked={false} onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole('switch'), { key: 'a' });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('renders label when provided', () => {
    render(<ToggleSwitch checked={false} onChange={() => {}} label="Enable feature" />);
    expect(screen.getByText('Enable feature')).toBeInTheDocument();
  });

  it('does not render label when not provided', () => {
    render(<ToggleSwitch checked={false} onChange={() => {}} />);
    expect(screen.queryByText(/./)).toBeNull();
  });

  it('is keyboard focusable', () => {
    render(<ToggleSwitch checked={false} onChange={() => {}} />);
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('tabindex', '0');
  });
});
