'use client';
import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import Avatar from '../Avatar';

describe('Avatar', () => {
  describe('Rendering', () => {
    it('renders image avatar', () => {
      render(<Avatar src="/avatar.jpg" alt="User avatar" />);
      const img = screen.getByRole('img');
      expect(img).toHaveAttribute('src', '/avatar.jpg');
      expect(img).toHaveAttribute('alt', 'User avatar');
    });

    it('renders initials when no image provided', () => {
      render(<Avatar name="John Doe" />);
      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('renders single initial for single name', () => {
      render(<Avatar name="John" />);
      expect(screen.getByText('J')).toBeInTheDocument();
    });

    it('renders icon when no image or name provided', () => {
      const { container } = render(<Avatar />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = render(<Avatar size="small" name="JD" />);
      const avatar = container.firstChild as HTMLElement;
      expect(avatar.style.width).toBe('32px');
      expect(avatar.style.height).toBe('32px');
    });

    it('renders medium size by default', () => {
      const { container } = render(<Avatar name="JD" />);
      const avatar = container.firstChild as HTMLElement;
      expect(avatar.style.width).toBe('40px');
      expect(avatar.style.height).toBe('40px');
    });

    it('renders large size', () => {
      const { container } = render(<Avatar size="large" name="JD" />);
      const avatar = container.firstChild as HTMLElement;
      expect(avatar.style.width).toBe('48px');
      expect(avatar.style.height).toBe('48px');
    });
  });

  describe('Shapes', () => {
    it('renders circle shape by default', () => {
      const { container } = render(<Avatar name="JD" />);
      const avatar = container.firstChild as HTMLElement;
      expect(avatar.style.borderRadius).toBe('50%');
    });

    it('renders square shape', () => {
      const { container } = render(<Avatar shape="square" name="JD" />);
      const avatar = container.firstChild as HTMLElement;
      expect(avatar.style.borderRadius).toBe('var(--ae-radius-md)');
    });
  });

  describe('Accessibility', () => {
    it('has aria-label with name', () => {
      render(<Avatar name="John Doe" />);
      expect(screen.getByLabelText('John Doe')).toBeInTheDocument();
    });

    it('has aria-label with alt text', () => {
      render(<Avatar src="/avatar.jpg" alt="User profile" />);
      expect(screen.getByLabelText('User profile')).toBeInTheDocument();
    });

    it('has default aria-label when no name or alt', () => {
      render(<Avatar />);
      expect(screen.getByLabelText('User avatar')).toBeInTheDocument();
    });

    it('supports custom aria-label', () => {
      render(<Avatar name="JD" aria-label="Admin user" />);
      expect(screen.getByLabelText('Admin user')).toBeInTheDocument();
    });
  });

  describe('Image Error Handling', () => {
    it('falls back to initials on image error', () => {
      render(<Avatar src="/broken.jpg" name="John Doe" alt="User" />);
      const img = screen.getByRole('img');
      act(() => {
        fireEvent.error(img);
      });
      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('falls back to icon when image fails and no name', () => {
      const { container } = render(<Avatar src="/broken.jpg" />);
      const img = screen.getByRole('img');
      act(() => {
        fireEvent.error(img);
      });
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });
});
