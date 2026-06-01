import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ChatMessage from '../ChatMessage';
import type { ChatMessage as ChatMessageType } from '@/types';

// Mock MarkdownRenderer since it has heavy dependencies
jest.mock('../MarkdownRenderer', () => {
  return function MockMarkdownRenderer({ content }: { content: string }) {
    return <div data-testid="markdown-content">{content}</div>;
  };
});

const baseMessage: ChatMessageType = {
  id: 'msg-1',
  role: 'assistant',
  content: 'Hello, how can I help?',
  created_at: '2024-01-15T10:30:00Z',
};

describe('ChatMessage', () => {
  describe('user messages', () => {
    it('renders user message with plain text', () => {
      const msg: ChatMessageType = { ...baseMessage, role: 'user', content: 'Hi there' };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('Hi there')).toBeInTheDocument();
    });

    it('displays "You" as the user name', () => {
      const msg: ChatMessageType = { ...baseMessage, role: 'user' };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('You')).toBeInTheDocument();
    });

    it('does not use MarkdownRenderer for user messages', () => {
      const msg: ChatMessageType = { ...baseMessage, role: 'user' };
      render(<ChatMessage message={msg} />);
      expect(screen.queryByTestId('markdown-content')).not.toBeInTheDocument();
    });
  });

  describe('assistant messages', () => {
    it('renders assistant message using MarkdownRenderer', () => {
      render(<ChatMessage message={baseMessage} />);
      expect(screen.getByTestId('markdown-content')).toHaveTextContent('Hello, how can I help?');
    });

    it('displays agent name when provided', () => {
      const msg: ChatMessageType = { ...baseMessage, agent_name: 'Support Bot' };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('Support Bot')).toBeInTheDocument();
    });

    it('displays "Assistant" as fallback name when agent_name is absent', () => {
      render(<ChatMessage message={baseMessage} />);
      expect(screen.getByText('Assistant')).toBeInTheDocument();
    });
  });

  describe('timestamp formatting', () => {
    it('renders a formatted time', () => {
      render(<ChatMessage message={baseMessage} />);
      // The time should be rendered (format depends on locale, but should contain digits)
      const timeEl = document.querySelector('.ant-typography.ant-typography-secondary');
      expect(timeEl).toBeInTheDocument();
    });
  });

  describe('status tags', () => {
    it('shows completed status tag', () => {
      const msg: ChatMessageType = { ...baseMessage, status: 'completed' };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('completed')).toBeInTheDocument();
    });

    it('shows failed status tag', () => {
      const msg: ChatMessageType = { ...baseMessage, status: 'failed' };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('failed')).toBeInTheDocument();
    });

    it('shows running status tag', () => {
      const msg: ChatMessageType = { ...baseMessage, status: 'running' };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('running')).toBeInTheDocument();
    });

    it('does not render status tag when status is undefined', () => {
      render(<ChatMessage message={baseMessage} />);
      expect(screen.queryByText('completed')).not.toBeInTheDocument();
      expect(screen.queryByText('failed')).not.toBeInTheDocument();
      expect(screen.queryByText('running')).not.toBeInTheDocument();
    });
  });

  describe('streaming', () => {
    it('shows streaming cursor when streaming is true on assistant message', () => {
      render(<ChatMessage message={baseMessage} streaming={true} />);
      // The blinking cursor is an inline span, check the style injection
      expect(document.querySelector('style')).toBeInTheDocument();
    });

    it('shows stop button when streaming and onStop provided', () => {
      const onStop = jest.fn();
      render(<ChatMessage message={baseMessage} streaming={true} onStop={onStop} />);
      expect(screen.getByText('Stop Generating')).toBeInTheDocument();
    });

    it('calls onStop when stop button is clicked', () => {
      const onStop = jest.fn();
      render(<ChatMessage message={baseMessage} streaming={true} onStop={onStop} />);
      fireEvent.click(screen.getByText('Stop Generating'));
      expect(onStop).toHaveBeenCalledTimes(1);
    });

    it('does not show stop button for user messages even when streaming', () => {
      const msg: ChatMessageType = { ...baseMessage, role: 'user' };
      render(<ChatMessage message={msg} streaming={true} onStop={jest.fn()} />);
      expect(screen.queryByText('Stop Generating')).not.toBeInTheDocument();
    });

    it('does not show stop button without onStop callback', () => {
      render(<ChatMessage message={baseMessage} streaming={true} />);
      expect(screen.queryByText('Stop Generating')).not.toBeInTheDocument();
    });
  });

  describe('tool calls', () => {
    it('renders tool call names', () => {
      const msg: ChatMessageType = {
        ...baseMessage,
        tool_calls: [
          { function: { name: 'web_search' }, output: 'Search results here', status: 'completed' },
        ],
      };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('web_search')).toBeInTheDocument();
    });

    it('renders tool call output', () => {
      const msg: ChatMessageType = {
        ...baseMessage,
        tool_calls: [
          { function: { name: 'calculator' }, output: '42', status: 'completed' },
        ],
      };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('renders multiple tool calls', () => {
      const msg: ChatMessageType = {
        ...baseMessage,
        tool_calls: [
          { function: { name: 'tool_a' }, status: 'completed' },
          { function: { name: 'tool_b' }, status: 'running' },
        ],
      };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('tool_a')).toBeInTheDocument();
      expect(screen.getByText('tool_b')).toBeInTheDocument();
    });

    it('shows "Tool Call" as fallback when function name is missing', () => {
      const msg: ChatMessageType = {
        ...baseMessage,
        tool_calls: [{ status: 'running' }],
      };
      render(<ChatMessage message={msg} />);
      expect(screen.getByText('Tool Call')).toBeInTheDocument();
    });

    it('does not render tool calls section when empty', () => {
      const msg: ChatMessageType = { ...baseMessage, tool_calls: [] };
      render(<ChatMessage message={msg} />);
      // No tool call tags should be present
      expect(screen.queryByText('Tool Call')).not.toBeInTheDocument();
    });
  });
});
