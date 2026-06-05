import React from 'react';
import { render, screen } from '@testing-library/react';
import Skeleton from '../Skeleton';

describe('Skeleton', () => {
  describe('Rendering', () => {
    it('renders a skeleton element', () => {
      const { container } = render(<Skeleton />);
      expect(container.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    });

    it('renders with default text variant', () => {
      const { container } = render(<Skeleton />);
      const el = container.querySelector('[aria-hidden="true"]') as HTMLElement;
      expect(el.style.height).toBe('16px');
    });

    it('renders circular variant', () => {
      const { container } = render(<Skeleton variant="circular" width={40} height={40} />);
      const el = container.querySelector('[aria-hidden="true"]') as HTMLElement;
      expect(el.style.borderRadius).toBe('50%');
    });

    it('renders rectangular variant', () => {
      const { container } = render(<Skeleton variant="rectangular" width={200} height={100} />);
      const el = container.querySelector('[aria-hidden="true"]') as HTMLElement;
      expect(el.style.width).toBe('200px');
      expect(el.style.height).toBe('100px');
    });

    it('renders multiple lines', () => {
      const { container } = render(<Skeleton lines={3} />);
      const elements = container.querySelectorAll('[aria-hidden="true"]');
      expect(elements).toHaveLength(3);
    });

    it('last line is 60% width for multi-line', () => {
      const { container } = render(<Skeleton lines={3} />);
      const elements = container.querySelectorAll('[aria-hidden="true"]');
      const last = elements[elements.length - 1] as HTMLElement;
      expect(last.style.width).toBe('60%');
    });
  });

  describe('Animation', () => {
    it('applies animation by default', () => {
      const { container } = render(<Skeleton />);
      const el = container.querySelector('[aria-hidden="true"]') as HTMLElement;
      expect(el.style.animation).toContain('skeleton-shimmer');
    });

    it('disables animation when animate is false', () => {
      const { container } = render(<Skeleton animate={false} />);
      const el = container.querySelector('[aria-hidden="true"]') as HTMLElement;
      expect(el.style.animation).toBe('none');
    });
  });

  describe('Accessibility', () => {
    it('has aria-hidden on skeleton elements', () => {
      const { container } = render(<Skeleton />);
      expect(container.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    });

    it('does not interfere with screen readers', () => {
      render(<Skeleton />);
      expect(screen.queryByRole('presentation')).not.toBeInTheDocument();
    });
  });
});
