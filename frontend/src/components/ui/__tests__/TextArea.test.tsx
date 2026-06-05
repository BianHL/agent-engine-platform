import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TextArea from '../TextArea';

describe('TextArea', () => {
  it('renders textarea', () => {
    render(<TextArea />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders label', () => {
    render(<TextArea label="Description" />);
    expect(screen.getByText('Description')).toBeInTheDocument();
  });

  it('renders hint text', () => {
    render(<TextArea hint="Max 500 chars" />);
    expect(screen.getByText('Max 500 chars')).toBeInTheDocument();
  });

  it('renders error text with role=alert', () => {
    render(<TextArea error="Required field" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Required field');
  });

  it('sets aria-invalid when error present', () => {
    render(<TextArea error="Bad input" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('does not set aria-invalid without error', () => {
    render(<TextArea />);
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'false');
  });

  it('associates error with textarea via aria-describedby', () => {
    render(<TextArea error="Too short" />);
    const textarea = screen.getByRole('textbox');
    const errorId = textarea.getAttribute('aria-describedby');
    expect(errorId).toBeTruthy();
    expect(document.getElementById(errorId!)).toHaveTextContent('Too short');
  });

  it('prefers error over hint', () => {
    render(<TextArea hint="Helpful text" error="Error text" />);
    expect(screen.getByText('Error text')).toBeInTheDocument();
    expect(screen.queryByText('Helpful text')).not.toBeInTheDocument();
  });

  it('forwards onChange', () => {
    const onChange = jest.fn();
    render(<TextArea onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } });
    expect(onChange).toHaveBeenCalled();
  });

  it('forwards placeholder', () => {
    render(<TextArea placeholder="Type here" />);
    expect(screen.getByPlaceholderText('Type here')).toBeInTheDocument();
  });

  it('has accessible label association', () => {
    render(<TextArea label="Notes" />);
    const label = screen.getByText('Notes');
    const textarea = screen.getByRole('textbox');
    expect(label).toHaveAttribute('for', textarea.id);
  });
});
