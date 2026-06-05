import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Tooltip from '../Tooltip';

describe('Tooltip Accessibility', () => {
  it('should have role="tooltip" on content', async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    );

    const trigger = screen.getByRole('button');
    await user.hover(trigger);

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toBeInTheDocument();
    expect(tooltip).toHaveTextContent('Tooltip text');
  });

  it('should have aria-describedby on trigger when visible', async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    );

    const trigger = screen.getByRole('button');
    await user.hover(trigger);

    const tooltip = screen.getByRole('tooltip');
    const tooltipId = tooltip.getAttribute('id');
    expect(trigger).toHaveAttribute('aria-describedby', tooltipId);
  });

  it('should have unique id on tooltip', async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    );

    const trigger = screen.getByRole('button');
    await user.hover(trigger);

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toHaveAttribute('id');
    expect(tooltip.getAttribute('id')).toBeTruthy();
  });

  it('should render tooltip content', () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    );

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toHaveTextContent('Tooltip text');
  });
});
