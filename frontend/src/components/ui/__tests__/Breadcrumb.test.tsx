import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Breadcrumb from '../Breadcrumb';

describe('Breadcrumb', () => {
  const items = [
    { label: 'Home', href: '/' },
    { label: 'Agents', href: '/agents' },
    { label: 'Detail' },
  ];

  describe('Rendering', () => {
    it('renders all items', () => {
      render(<Breadcrumb items={items} />);
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Agents')).toBeInTheDocument();
      expect(screen.getByText('Detail')).toBeInTheDocument();
    });

    it('renders links for items with href', () => {
      render(<Breadcrumb items={items} />);
      expect(screen.getByText('Home').closest('a')).toHaveAttribute('href', '/');
      expect(screen.getByText('Agents').closest('a')).toHaveAttribute('href', '/agents');
    });

    it('renders last item as plain text', () => {
      render(<Breadcrumb items={items} />);
      const detail = screen.getByText('Detail');
      expect(detail.tagName).not.toBe('A');
      expect(detail.closest('button')).toBeNull();
    });

    it('renders custom separator', () => {
      render(<Breadcrumb items={items} separator=">" />);
      expect(screen.getAllByText('>')).toHaveLength(2);
    });

    it('renders default separator', () => {
      render(<Breadcrumb items={items} />);
      expect(screen.getAllByText('/')).toHaveLength(2);
    });
  });

  describe('Interaction', () => {
    it('calls onClick for button items', () => {
      const onClick = jest.fn();
      const buttonItems = [
        { label: 'Home', onClick },
        { label: 'Current' },
      ];
      render(<Breadcrumb items={buttonItems} />);
      fireEvent.click(screen.getByText('Home'));
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has navigation role with aria-label', () => {
      render(<Breadcrumb items={items} />);
      expect(screen.getByLabelText('Breadcrumb')).toBeInTheDocument();
    });

    it('marks last item with aria-current="page"', () => {
      render(<Breadcrumb items={items} />);
      expect(screen.getByText('Detail')).toHaveAttribute('aria-current', 'page');
    });

    it('separator has aria-hidden', () => {
      render(<Breadcrumb items={items} />);
      const separators = screen.getAllByText('/');
      separators.forEach((sep) => {
        expect(sep).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });
});
