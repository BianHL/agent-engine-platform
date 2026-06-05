import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Table from '../Table';

interface TestRow extends Record<string, unknown> {
  id: number;
  name: string;
  status: string;
}

describe('Table', () => {
  const columns = [
    { key: 'name', title: 'Name' },
    { key: 'status', title: 'Status' },
  ];

  const data: TestRow[] = [
    { id: 1, name: 'Alice', status: 'active' },
    { id: 2, name: 'Bob', status: 'inactive' },
  ];

  describe('Rendering', () => {
    it('renders column headers', () => {
      render(<Table data={data} columns={columns} />);
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
    });

    it('renders data rows', () => {
      render(<Table data={data} columns={columns} />);
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });

    it('renders empty state message', () => {
      render(<Table data={[]} columns={columns} />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });

    it('renders custom empty message', () => {
      render(<Table data={[]} columns={columns} emptyMessage="Nothing here" />);
      expect(screen.getByText('Nothing here')).toBeInTheDocument();
    });

    it('renders custom cell content via render function', () => {
      const customColumns = [
        { key: 'name', title: 'Name', render: (row: TestRow) => <strong>{row.name}</strong> },
      ];
      render(<Table data={data} columns={customColumns} />);
      expect(screen.getByText('Alice').tagName).toBe('STRONG');
    });
  });

  describe('Accessibility', () => {
    it('renders a table element', () => {
      render(<Table data={data} columns={columns} />);
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders column headers as th elements', () => {
      render(<Table data={data} columns={columns} />);
      const headers = screen.getAllByRole('columnheader');
      expect(headers).toHaveLength(2);
    });
  });

  describe('Loading State', () => {
    it('shows loading overlay when loading is true', () => {
      render(<Table data={data} columns={columns} loading />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('does not show loading overlay when loading is false', () => {
      render(<Table data={data} columns={columns} />);
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    it('still renders data when loading', () => {
      render(<Table data={data} columns={columns} loading />);
      expect(screen.getByText('Alice')).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('renders sort indicator on sortable columns', () => {
      const sortableColumns = [
        { key: 'name', title: 'Name', sortable: true },
        { key: 'status', title: 'Status' },
      ];
      render(<Table data={data} columns={sortableColumns} />);
      const nameHeader = screen.getByText('Name').closest('th')!;
      expect(nameHeader.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    });

    it('calls onSort when sortable header is clicked', () => {
      const onSort = jest.fn();
      const sortableColumns = [
        { key: 'name', title: 'Name', sortable: true },
        { key: 'status', title: 'Status' },
      ];
      render(<Table data={data} columns={sortableColumns} onSort={onSort} />);
      fireEvent.click(screen.getByText('Name'));
      expect(onSort).toHaveBeenCalledWith('name', 'asc');
    });

    it('toggles sort direction when parent updates sortDirection prop', () => {
      const onSort = jest.fn();
      const sortableColumns = [
        { key: 'name', title: 'Name', sortable: true },
      ];
      const { rerender } = render(<Table data={data} columns={sortableColumns} onSort={onSort} />);
      // First click: no sortKey set, so next direction is 'asc'
      fireEvent.click(screen.getByText('Name'));
      expect(onSort).toHaveBeenNthCalledWith(1, 'name', 'asc');

      // Parent updates props after first click
      rerender(<Table data={data} columns={sortableColumns} onSort={onSort} sortKey="name" sortDirection="asc" />);
      // Second click: sortKey matches, sortDirection is 'asc', so next is 'desc'
      fireEvent.click(screen.getByText('Name'));
      expect(onSort).toHaveBeenNthCalledWith(2, 'name', 'desc');
    });

    it('shows current sort direction indicator', () => {
      const sortableColumns = [
        { key: 'name', title: 'Name', sortable: true },
      ];
      render(<Table data={data} columns={sortableColumns} sortKey="name" sortDirection="asc" />);
      const nameHeader = screen.getByText('Name').closest('th')!;
      expect(nameHeader.textContent).toContain('↑');
    });
  });
});
