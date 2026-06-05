import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Pagination from '../Pagination';

describe('Pagination', () => {
  describe('Rendering', () => {
    it('renders page buttons', () => {
      render(<Pagination current={1} total={50} onChange={() => {}} />);
      expect(screen.getByLabelText('Page 1')).toBeInTheDocument();
    });

    it('renders previous and next buttons', () => {
      render(<Pagination current={2} total={50} onChange={() => {}} />);
      expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
      expect(screen.getByLabelText('Next page')).toBeInTheDocument();
    });

    it('renders correct number of pages for small total', () => {
      render(<Pagination current={1} total={30} pageSize={10} onChange={() => {}} />);
      expect(screen.getByLabelText('Page 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Page 2')).toBeInTheDocument();
      expect(screen.getByLabelText('Page 3')).toBeInTheDocument();
    });
  });

  describe('Interaction', () => {
    it('calls onChange when page is clicked', () => {
      const onChange = jest.fn();
      render(<Pagination current={1} total={50} onChange={onChange} />);
      fireEvent.click(screen.getByLabelText('Page 2'));
      expect(onChange).toHaveBeenCalledWith(2);
    });

    it('calls onChange with previous page', () => {
      const onChange = jest.fn();
      render(<Pagination current={3} total={50} onChange={onChange} />);
      fireEvent.click(screen.getByLabelText('Previous page'));
      expect(onChange).toHaveBeenCalledWith(2);
    });

    it('calls onChange with next page', () => {
      const onChange = jest.fn();
      render(<Pagination current={1} total={50} onChange={onChange} />);
      fireEvent.click(screen.getByLabelText('Next page'));
      expect(onChange).toHaveBeenCalledWith(2);
    });

    it('disables previous button on first page', () => {
      render(<Pagination current={1} total={50} onChange={() => {}} />);
      expect(screen.getByLabelText('Previous page')).toBeDisabled();
    });

    it('disables next button on last page', () => {
      render(<Pagination current={5} total={50} pageSize={10} onChange={() => {}} />);
      expect(screen.getByLabelText('Next page')).toBeDisabled();
    });
  });

  describe('Current Page Indicator', () => {
    it('marks current page with aria-current', () => {
      render(<Pagination current={2} total={50} onChange={() => {}} />);
      expect(screen.getByLabelText('Page 2')).toHaveAttribute('aria-current', 'page');
    });

    it('does not mark non-current pages', () => {
      render(<Pagination current={2} total={50} onChange={() => {}} />);
      expect(screen.getByLabelText('Page 1')).not.toHaveAttribute('aria-current');
    });
  });

  describe('Ellipsis', () => {
    it('shows ellipsis for many pages', () => {
      render(<Pagination current={5} total={200} pageSize={10} onChange={() => {}} />);
      expect(screen.getAllByText('…').length).toBeGreaterThan(0);
    });
  });

  describe('Size Changer', () => {
    it('shows size changer when enabled', () => {
      render(
        <Pagination
          current={1}
          total={50}
          showSizeChanger
          onPageSizeChange={() => {}}
          onChange={() => {}}
        />
      );
      expect(screen.getByLabelText('Items per page')).toBeInTheDocument();
    });

    it('does not show size changer by default', () => {
      render(<Pagination current={1} total={50} onChange={() => {}} />);
      expect(screen.queryByLabelText('Items per page')).not.toBeInTheDocument();
    });

    it('calls onPageSizeChange when size is changed', () => {
      const onPageSizeChange = jest.fn();
      render(
        <Pagination
          current={1}
          total={50}
          showSizeChanger
          onPageSizeChange={onPageSizeChange}
          onChange={() => {}}
        />
      );
      fireEvent.change(screen.getByLabelText('Items per page'), { target: { value: '20' } });
      expect(onPageSizeChange).toHaveBeenCalledWith(20);
    });
  });

  describe('Accessibility', () => {
    it('has navigation role', () => {
      render(<Pagination current={1} total={50} onChange={() => {}} />);
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('has aria-label on navigation', () => {
      render(<Pagination current={1} total={50} onChange={() => {}} />);
      expect(screen.getByLabelText('Pagination')).toBeInTheDocument();
    });
  });
});
