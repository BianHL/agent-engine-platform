'use client';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Tabs from '../Tabs';

describe('Tabs', () => {
  const items = [
    { key: 'overview', label: 'Overview' },
    { key: 'settings', label: 'Settings' },
    { key: 'members', label: 'Members', disabled: true },
  ];

  describe('Rendering', () => {
    it('renders all tab labels', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Members')).toBeInTheDocument();
    });

    it('renders children content', () => {
      render(
        <Tabs items={items} activeKey="overview" onChange={() => {}}>
          <div>Overview content</div>
        </Tabs>
      );
      expect(screen.getByText('Overview content')).toBeInTheDocument();
    });
  });

  describe('Active State', () => {
    it('applies active style to selected tab', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      const tab = screen.getByText('Overview');
      expect(tab.getAttribute('aria-selected')).toBe('true');
    });

    it('applies inactive style to non-selected tabs', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      const tab = screen.getByText('Settings');
      expect(tab.getAttribute('aria-selected')).toBe('false');
    });
  });

  describe('Interaction', () => {
    it('calls onChange when tab is clicked', () => {
      const onChange = jest.fn();
      render(<Tabs items={items} activeKey="overview" onChange={onChange} />);
      fireEvent.click(screen.getByText('Settings'));
      expect(onChange).toHaveBeenCalledWith('settings');
    });

    it('does not call onChange for disabled tabs', () => {
      const onChange = jest.fn();
      render(<Tabs items={items} activeKey="overview" onChange={onChange} />);
      fireEvent.click(screen.getByText('Members'));
      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has role=tablist on container', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });

    it('has role=tab on each tab', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      const tabs = screen.getAllByRole('tab');
      expect(tabs).toHaveLength(3);
    });

    it('has aria-selected on tabs', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      const tabs = screen.getAllByRole('tab');
      expect(tabs[0]).toHaveAttribute('aria-selected', 'true');
      expect(tabs[1]).toHaveAttribute('aria-selected', 'false');
    });

    it('has aria-disabled on disabled tabs', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      const disabledTab = screen.getByText('Members').closest('[role="tab"]');
      expect(disabledTab).toHaveAttribute('aria-disabled', 'true');
    });

    it('has tabIndex on tabs', () => {
      render(<Tabs items={items} activeKey="overview" onChange={() => {}} />);
      const tabs = screen.getAllByRole('tab');
      tabs.forEach((tab) => {
        expect(tab).toHaveAttribute('tabindex');
      });
    });
  });
});
