'use client';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Dropdown from '../Dropdown';

describe('Dropdown', () => {
  const items = [
    { key: '1', label: 'Option 1' },
    { key: '2', label: 'Option 2' },
    { key: '3', label: 'Option 3', disabled: true },
  ];

  describe('Rendering', () => {
    it('renders trigger element', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('does not show menu items initially', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      expect(screen.queryByText('Option 1')).not.toBeInTheDocument();
    });
  });

  describe('Toggle', () => {
    it('shows menu on click', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      expect(screen.getByText('Option 1')).toBeInTheDocument();
      expect(screen.getByText('Option 2')).toBeInTheDocument();
    });

    it('hides menu on second click', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      fireEvent.click(screen.getByText('Click me'));
      expect(screen.queryByText('Option 1')).not.toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    it('calls onSelect when item is clicked', () => {
      const onSelect = jest.fn();
      render(
        <Dropdown items={items} onSelect={onSelect}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      fireEvent.click(screen.getByText('Option 1'));
      expect(onSelect).toHaveBeenCalledWith('1');
    });

    it('does not call onSelect for disabled items', () => {
      const onSelect = jest.fn();
      render(
        <Dropdown items={items} onSelect={onSelect}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      fireEvent.click(screen.getByText('Option 3'));
      expect(onSelect).not.toHaveBeenCalled();
    });

    it('closes menu after selection', () => {
      const onSelect = jest.fn();
      render(
        <Dropdown items={items} onSelect={onSelect}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      fireEvent.click(screen.getByText('Option 1'));
      expect(screen.queryByText('Option 1')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has aria-expanded on trigger', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      const trigger = screen.getByText('Click me').closest('[aria-expanded]');
      expect(trigger).toHaveAttribute('aria-expanded', 'false');
    });

    it('has aria-haspopup on trigger', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      const trigger = screen.getByText('Click me').closest('[aria-haspopup]');
      expect(trigger).toHaveAttribute('aria-haspopup', 'menu');
    });

    it('has role=menu on dropdown', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      expect(screen.getByRole('menu')).toBeInTheDocument();
    });

    it('has role=menuitem on items', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems).toHaveLength(3);
    });

    it('disabled items have aria-disabled', () => {
      render(
        <Dropdown items={items} onSelect={() => {}}>
          <button>Click me</button>
        </Dropdown>
      );
      fireEvent.click(screen.getByText('Click me'));
      const disabledItem = screen.getByText('Option 3').closest('[aria-disabled]');
      expect(disabledItem).toHaveAttribute('aria-disabled', 'true');
    });
  });
});
