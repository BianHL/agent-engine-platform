import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock ESM dependencies that Jest cannot parse
jest.mock('react-markdown', () => {
  return function ReactMarkdown({ children, components }: any) {
    // Simple mock: render content as a div, simulate basic markdown
    const content = children || '';
    // Simulate code blocks
    const codeBlockMatch = content.match(/```(\w+)\n([\s\S]*?)```/);
    if (codeBlockMatch && components?.code) {
      const lang = codeBlockMatch[1];
      const code = codeBlockMatch[2];
      return components.code({ className: `lang-${lang}`, children: code });
    }
    // Simulate links
    const linkMatch = content.match(/\[(.+?)\]\((.+?)\)/);
    if (linkMatch && components?.a) {
      return components.a({ href: linkMatch[2], children: linkMatch[1] });
    }
    // Simulate blockquotes
    const blockquoteMatch = content.match(/^>\s*(.+)/m);
    if (blockquoteMatch && components?.blockquote) {
      return components.blockquote({ children: blockquoteMatch[1] });
    }
    // Default: just render the text
    return <div>{content}</div>;
  };
});

jest.mock('remark-gfm', () => () => {});
jest.mock('rehype-sanitize', () => () => {});

// Mock highlight.js
jest.mock('highlight.js', () => ({
  highlight: jest.fn((code: string, opts: any) => ({ value: `<span class="hljs">${code}</span>` })),
}));

// Mock highlight.js CSS import
jest.mock('highlight.js/styles/github-dark.css', () => ({}));

import MarkdownRenderer from '../MarkdownRenderer';

describe('MarkdownRenderer', () => {
  it('renders plain text content', () => {
    render(<MarkdownRenderer content="Hello world" />);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<MarkdownRenderer content="text" className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders empty content without crashing', () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container).toBeTruthy();
  });

  it('renders code blocks with language label and copy button', () => {
    const codeMd = '```javascript\nconsole.log("hi")\n```';
    render(<MarkdownRenderer content={codeMd} />);
    // DOM text is lowercase; CSS text-transform: uppercase handles display
    expect(screen.getByText('javascript')).toBeInTheDocument();
    expect(screen.getByText('Copy')).toBeInTheDocument();
  });

  it('copy button changes text to "Copied!" when clicked', () => {
    Object.assign(navigator, {
      clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
    });

    const codeMd = '```python\nprint("hi")\n```';
    render(<MarkdownRenderer content={codeMd} />);
    fireEvent.click(screen.getByText('Copy'));
    expect(screen.getByText('Copied!')).toBeInTheDocument();
  });

  it('renders links with target blank', () => {
    render(<MarkdownRenderer content="[click me](https://example.com)" />);
    const link = screen.getByText('click me');
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders blockquotes with custom styling', () => {
    render(<MarkdownRenderer content="> quoted text" />);
    expect(screen.getByText('quoted text')).toBeInTheDocument();
    const blockquote = document.querySelector('blockquote');
    expect(blockquote).toBeInTheDocument();
  });

  it('renders content with word break style', () => {
    const { container } = render(<MarkdownRenderer content="text" />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.style.lineHeight).toBe('1.6');
    expect(wrapper.style.wordBreak).toBe('break-word');
  });
});
