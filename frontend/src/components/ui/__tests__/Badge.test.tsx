'use client';
import React from 'react';
import { render, screen } from '@testing-library/react';
import Badge from '../Badge';

describe('Badge', () => {
  describe('Rendering', () => {
    it('renders children with badge content', () => {
      render(
        <Badge count={5}>
          <span>Notifications</span>
        </Badge>
      );
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('renders without badge when count is 0 and showZero is false', () => {
      render(
        <Badge count={0}>
          <span>Notifications</span>
        </Badge>
      );
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.queryByText('0')).not.toBeInTheDocument();
    });

    it('renders zero when showZero is true', () => {
      render(
        <Badge count={0} showZero>
          <span>Notifications</span>
        </Badge>
      );
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('renders dot variant when variant is dot', () => {
      const { container } = render(
        <Badge variant="dot">
          <span>Notifications</span>
        </Badge>
      );
      const dot = container.querySelector('[aria-label="New notification"]');
      expect(dot).toBeInTheDocument();
    });
  });

  describe('Count Display', () => {
    it('displays count when less than overflowCount', () => {
      render(
        <Badge count={99}>
          <span>Messages</span>
        </Badge>
      );
      expect(screen.getByText('99')).toBeInTheDocument();
    });

    it('displays overflowCount+ when count exceeds overflowCount', () => {
      render(
        <Badge count={100} overflowCount={99}>
          <span>Messages</span>
        </Badge>
      );
      expect(screen.getByText('99+')).toBeInTheDocument();
    });

    it('uses default overflowCount of 99', () => {
      render(
        <Badge count={1000}>
          <span>Messages</span>
        </Badge>
      );
      expect(screen.getByText('99+')).toBeInTheDocument();
    });
  });

  describe('Color Variants', () => {
    it('applies default color style', () => {
      const { container } = render(
        <Badge count={5}>
          <span>Test</span>
        </Badge>
      );
      const badge = container.querySelector('[aria-label]');
      expect(badge).toBeInTheDocument();
    });

    it('applies success color', () => {
      const { container } = render(
        <Badge count={5} color="success">
          <span>Test</span>
        </Badge>
      );
      const badge = container.querySelector('[aria-label]');
      expect(badge).toBeInTheDocument();
    });

    it('applies warning color', () => {
      const { container } = render(
        <Badge count={5} color="warning">
          <span>Test</span>
        </Badge>
      );
      const badge = container.querySelector('[aria-label]');
      expect(badge).toBeInTheDocument();
    });

    it('applies error color', () => {
      const { container } = render(
        <Badge count={5} color="error">
          <span>Test</span>
        </Badge>
      );
      const badge = container.querySelector('[aria-label]');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has aria-label with count', () => {
      render(
        <Badge count={5}>
          <span>Notifications</span>
        </Badge>
      );
      expect(screen.getByLabelText('5 notifications')).toBeInTheDocument();
    });

    it('has aria-label for dot variant', () => {
      render(
        <Badge variant="dot">
          <span>Notifications</span>
        </Badge>
      );
      expect(screen.getByLabelText('New notification')).toBeInTheDocument();
    });

    it('supports custom aria-label', () => {
      render(
        <Badge count={3} aria-label="3 unread messages">
          <span>Inbox</span>
        </Badge>
      );
      expect(screen.getByLabelText('3 unread messages')).toBeInTheDocument();
    });
  });

  describe('Standalone Badge', () => {
    it('renders standalone badge without children', () => {
      render(<Badge count={5} />);
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('renders standalone dot badge', () => {
      const { container } = render(<Badge variant="dot" />);
      const dot = container.querySelector('[aria-label="New notification"]');
      expect(dot).toBeInTheDocument();
    });
  });
});
