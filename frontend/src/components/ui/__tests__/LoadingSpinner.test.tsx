import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders a spinner by default', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector('.ant-spin')).toBeInTheDocument();
  });

  it('renders with default large size', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector('.ant-spin-lg')).toBeInTheDocument();
  });

  it('renders with small size', () => {
    const { container } = render(<LoadingSpinner size="small" />);
    expect(container.querySelector('.ant-spin-sm')).toBeInTheDocument();
  });

  it('renders with default size', () => {
    const { container } = render(<LoadingSpinner size="default" />);
    // default size has neither sm nor lg class
    expect(container.querySelector('.ant-spin')).toBeInTheDocument();
    expect(container.querySelector('.ant-spin-sm')).not.toBeInTheDocument();
    expect(container.querySelector('.ant-spin-lg')).not.toBeInTheDocument();
  });

  it('renders without errors when tip is provided', () => {
    const { container } = render(<LoadingSpinner tip="Loading data..." fullScreen />);
    // antd Spin only renders tip text in nested (with children) mode
    expect(container.querySelector('.ant-spin')).toBeInTheDocument();
  });

  it('renders Spin component in all configurations', () => {
    const { container: c1 } = render(<LoadingSpinner />);
    const { container: c2 } = render(<LoadingSpinner fullScreen />);
    expect(c1.querySelector('.ant-spin')).toBeInTheDocument();
    expect(c2.querySelector('.ant-spin')).toBeInTheDocument();
  });

  it('applies fullScreen styles when fullScreen is true', () => {
    const { container } = render(<LoadingSpinner fullScreen />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.style.height).toBe('100%');
    expect(wrapper.style.minHeight).toBe('200px');
  });

  it('applies default padding when fullScreen is false', () => {
    const { container } = render(<LoadingSpinner />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.style.padding).toBe('40px 0px');
  });
});
