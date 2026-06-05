import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Input from '../Input';

describe('Input', () => {
  describe('Rendering', () => {
    it('renders input element', () => {
      render(<Input placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Input label="Username" />);
      expect(screen.getByText('Username')).toBeInTheDocument();
    });

    it('renders with error message', () => {
      render(<Input error="Required field" />);
      expect(screen.getByRole('alert')).toHaveTextContent('Required field');
    });

    it('renders with hint', () => {
      render(<Input hint="Must be at least 8 characters" />);
      expect(screen.getByText('Must be at least 8 characters')).toBeInTheDocument();
    });

    it('hides hint when error is present', () => {
      render(<Input hint="Help text" error="Error!" />);
      expect(screen.queryByText('Help text')).not.toBeInTheDocument();
      expect(screen.getByText('Error!')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('associates label with input via htmlFor', () => {
      render(<Input label="Email" />);
      const input = screen.getByLabelText('Email');
      expect(input).toBeInTheDocument();
    });

    it('sets aria-invalid when error is present', () => {
      render(<Input error="Invalid" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
    });

    it('sets aria-invalid to false when no error', () => {
      render(<Input />);
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'false');
    });

    it('sets aria-describedby for error', () => {
      render(<Input error="Required" />);
      const input = screen.getByRole('textbox');
      const describedBy = input.getAttribute('aria-describedby');
      expect(describedBy).toBeTruthy();
      expect(document.getElementById(describedBy!)).toHaveTextContent('Required');
    });

    it('sets aria-describedby for hint', () => {
      render(<Input hint="Help" />);
      const input = screen.getByRole('textbox');
      const describedBy = input.getAttribute('aria-describedby');
      expect(describedBy).toBeTruthy();
      expect(document.getElementById(describedBy!)).toHaveTextContent('Help');
    });
  });

  describe('Prefix/Suffix', () => {
    it('renders prefix element', () => {
      render(<Input prefix={<span>$</span>} />);
      expect(screen.getByText('$')).toBeInTheDocument();
    });

    it('renders suffix element', () => {
      render(<Input suffix={<span>USD</span>} />);
      expect(screen.getByText('USD')).toBeInTheDocument();
    });

    it('renders both prefix and suffix', () => {
      render(<Input prefix={<span>$</span>} suffix={<span>.00</span>} />);
      expect(screen.getByText('$')).toBeInTheDocument();
      expect(screen.getByText('.00')).toBeInTheDocument();
    });
  });

  describe('Allow Clear', () => {
    it('shows clear button when allowClear and value is present', () => {
      render(<Input allowClear value="hello" onChange={() => {}} />);
      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });

    it('does not show clear button when value is empty', () => {
      render(<Input allowClear value="" onChange={() => {}} />);
      expect(screen.queryByRole('button', { name: /clear/i })).not.toBeInTheDocument();
    });

    it('calls onChange with empty string when clear is clicked', () => {
      const onChange = jest.fn();
      render(<Input allowClear value="hello" onChange={onChange} />);
      fireEvent.click(screen.getByRole('button', { name: /clear/i }));
      expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ target: expect.objectContaining({ value: '' }) }));
    });
  });
});
