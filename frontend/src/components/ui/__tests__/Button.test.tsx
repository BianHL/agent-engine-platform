import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button';

describe('Button', () => {
  describe('Rendering', () => {
    it('renders children text', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button')).toHaveTextContent('Click me');
    });

    it('renders with default variant (primary)', () => {
      render(<Button>Test</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.background).toContain('var(--ae-gradient-primary)');
    });

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.border).toBe('1px solid var(--ae-line-strong)');
    });

    it('renders danger variant', () => {
      render(<Button variant="danger">Delete</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.background).toBe('var(--ae-danger)');
    });
  });

  describe('Sizes', () => {
    it('renders sm size', () => {
      render(<Button size="sm">Small</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.padding).toBe('8px 14px');
      expect(btn.style.fontSize).toBe('12px');
    });

    it('renders md size by default', () => {
      render(<Button>Medium</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.padding).toBe('12px 16px');
      expect(btn.style.fontSize).toBe('13px');
    });

    it('renders lg size', () => {
      render(<Button size="lg">Large</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.padding).toBe('14px 20px');
      expect(btn.style.fontSize).toBe('14px');
    });
  });

  describe('Interaction', () => {
    it('calls onClick when clicked', () => {
      const onClick = jest.fn();
      render(<Button onClick={onClick}>Click</Button>);
      fireEvent.click(screen.getByRole('button'));
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', () => {
      const onClick = jest.fn();
      render(<Button onClick={onClick} disabled>Click</Button>);
      fireEvent.click(screen.getByRole('button'));
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has aria-label', () => {
      render(<Button aria-label="Submit form">Submit</Button>);
      expect(screen.getByLabelText('Submit form')).toBeInTheDocument();
    });

    it('has aria-disabled when disabled', () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
    });

    it('has correct type attribute', () => {
      render(<Button type="submit">Submit</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
    });
  });

  describe('Loading State', () => {
    it('renders loading spinner when loading is true', () => {
      render(<Button loading>Submit</Button>);
      const btn = screen.getByRole('button');
      expect(btn.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    });

    it('sets aria-busy when loading', () => {
      render(<Button loading>Submit</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    });

    it('does not set aria-busy when not loading', () => {
      render(<Button>Submit</Button>);
      expect(screen.getByRole('button')).not.toHaveAttribute('aria-busy');
    });

    it('disables click handler when loading', () => {
      const onClick = jest.fn();
      render(<Button loading onClick={onClick}>Submit</Button>);
      fireEvent.click(screen.getByRole('button'));
      expect(onClick).not.toHaveBeenCalled();
    });

    it('shows reduced opacity when loading', () => {
      render(<Button loading>Submit</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.opacity).toBe('0.7');
    });

    it('prevents pointer events when loading', () => {
      render(<Button loading>Submit</Button>);
      const btn = screen.getByRole('button');
      expect(btn.style.pointerEvents).toBe('none');
    });
  });
});
