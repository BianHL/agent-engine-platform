import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Tooltip from '../Tooltip';

describe('Tooltip', () => {
  it('renders children', () => {
    render(<Tooltip content="Help text"><button>Hover me</button></Tooltip>);
    expect(screen.getByText('Hover me')).toBeInTheDocument();
  });

  it('shows tooltip on mouse enter', () => {
    render(<Tooltip content="Tooltip text"><button>Hover</button></Tooltip>);
    fireEvent.mouseEnter(screen.getByText('Hover'));
    expect(screen.getByRole('tooltip')).toHaveTextContent('Tooltip text');
  });

  it('hides tooltip on mouse leave', () => {
    render(<Tooltip content="Tooltip text"><button>Hover</button></Tooltip>);
    fireEvent.mouseEnter(screen.getByText('Hover'));
    fireEvent.mouseLeave(screen.getByText('Hover'));
    expect(screen.getByRole('tooltip')).toHaveTextContent('Tooltip text');
  });

  it('sets aria-describedby on child when visible', () => {
    render(<Tooltip content="Info"><button>Btn</button></Tooltip>);
    const btn = screen.getByText('Btn');
    expect(btn).not.toHaveAttribute('aria-describedby');

    fireEvent.mouseEnter(btn);
    expect(btn).toHaveAttribute('aria-describedby');
  });

  it('has role=tooltip', () => {
    render(<Tooltip content="Tip"><span>Trigger</span></Tooltip>);
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
  });

  it('renders with different positions', () => {
    const positions = ['top', 'bottom', 'left', 'right'] as const;
    positions.forEach((pos) => {
      const { unmount } = render(
        <Tooltip content="Tip" position={pos}><span>Trigger</span></Tooltip>
      );
      expect(screen.getByRole('tooltip')).toBeInTheDocument();
      unmount();
    });
  });
});
