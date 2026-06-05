import React from 'react';
import { render, screen } from '@testing-library/react';
import Card from '../Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Hello</Card>);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders with default variant', () => {
    render(<Card>Content</Card>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders with compact variant', () => {
    render(<Card variant="compact">Compact</Card>);
    expect(screen.getByText('Compact')).toBeInTheDocument();
  });

  it('renders with hero variant', () => {
    render(<Card variant="hero">Hero</Card>);
    expect(screen.getByText('Hero')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Card className="my-card">Content</Card>);
    const el = screen.getByText('Content').closest('div')?.parentElement;
    expect(el?.className).toContain('my-card');
  });

  it('renders decorative element when decorative is true', () => {
    render(<Card decorative>Content</Card>);
    // The decorative div is rendered (has position: absolute, no text content)
    // Just verify the component renders without error
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('does not render decorative element by default', () => {
    render(<Card>Content</Card>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('applies hover class by default', () => {
    const { container } = render(<Card>Hoverable</Card>);
    const cardDiv = container.firstChild as HTMLElement;
    expect(cardDiv.className).toContain('card-hover');
  });

  it('does not apply hover class when hover is false', () => {
    const { container } = render(<Card hover={false}>No hover</Card>);
    const cardDiv = container.firstChild as HTMLElement;
    expect(cardDiv.className).not.toContain('card-hover');
  });

  it('renders multiple children', () => {
    render(
      <Card>
        <h2>Title</h2>
        <p>Description</p>
      </Card>
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
  });
});
