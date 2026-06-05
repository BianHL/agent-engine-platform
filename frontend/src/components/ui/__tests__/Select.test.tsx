import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Select from '../Select';

const options = [
  { value: 'a', label: 'Option A' },
  { value: 'b', label: 'Option B' },
  { value: 'c', label: 'Option C' },
];

describe('Select', () => {
  it('renders options', () => {
    render(<Select options={options} />);
    expect(screen.getByText('Option A')).toBeInTheDocument();
    expect(screen.getByText('Option B')).toBeInTheDocument();
  });

  it('renders placeholder', () => {
    render(<Select options={options} />);
    expect(screen.getByText('Select...')).toBeInTheDocument();
  });

  it('renders custom placeholder', () => {
    render(<Select options={options} placeholder="Pick one" />);
    expect(screen.getByText('Pick one')).toBeInTheDocument();
  });

  it('renders label', () => {
    render(<Select options={options} label="Category" />);
    expect(screen.getByText('Category')).toBeInTheDocument();
  });

  it('calls onChange when selection changes', () => {
    const onChange = jest.fn();
    render(<Select options={options} onChange={onChange} />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'b' } });
    expect(onChange).toHaveBeenCalledWith('b');
  });

  it('renders with controlled value', () => {
    render(<Select options={options} value="b" />);
    expect(screen.getByRole('combobox')).toHaveValue('b');
  });

  it('has accessible label association', () => {
    render(<Select options={options} label="Color" />);
    const label = screen.getByText('Color');
    const select = screen.getByRole('combobox');
    expect(label).toHaveAttribute('for', select.id);
  });
});
