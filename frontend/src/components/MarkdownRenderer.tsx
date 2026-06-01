'use client';
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { Button } from 'antd';
import { CopyOutlined, CheckOutlined } from '@ant-design/icons';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const sanitizeSchema = {
  tagNames: [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'del', 'code', 'pre',
    'ul', 'ol', 'li',
    'blockquote',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span',
  ],
  attributes: {
    a: ['href', 'target', 'rel'],
    img: ['src', 'alt'],
    code: ['className'],
  },
};

// 代码块组件，支持语法高亮和复制按钮
function CodeBlock({ className, children, ...props }: any) {
  const language = className?.replace('lang-', '') || 'plaintext';
  const codeContent = String(children).replace(/\n$/, '');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 使用 highlight.js 进行语法高亮
  const highlighted = hljs.highlight(codeContent, { language: language === 'plaintext' ? 'plaintext' : language }).value;

  return (
    <div style={{ position: 'relative', marginBottom: 16 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 16px',
        background: '#24292e',
        borderBottom: '1px solid #3a3f44',
        borderTopLeftRadius: 6,
        borderTopRightRadius: 6,
        fontSize: 12,
        color: '#f0f6fc',
      }}>
        <span style={{ textTransform: 'uppercase', fontWeight: 500 }}>{language}</span>
        <Button
          type="text"
          size="small"
          icon={copied ? <CheckOutlined /> : <CopyOutlined />}
          onClick={handleCopy}
          style={{
            color: copied ? '#52c41a' : '#8b949e',
            border: 'none',
            padding: 0,
            height: 24,
            minWidth: 32,
          }}
        >
          {copied ? 'Copied!' : 'Copy'}
        </Button>
      </div>
      <pre
        style={{
          background: '#0d1117',
          padding: 16,
          borderRadius: '0 0 6px 6px',
          overflowX: 'auto',
          margin: 0,
          fontSize: 13,
          lineHeight: 1.5,
          borderTop: 'none',
        }}
        {...props}
      >
        <code
          className={`hljs language-${language}`}
          dangerouslySetInnerHTML={{ __html: highlighted }}
          style={{
            background: 'transparent',
            padding: 0,
            fontFamily: "'SF Mono', 'Consolas', 'Source Code Pro', monospace",
          }}
        />
      </pre>
    </div>
  );
}

export default function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={className} style={{ lineHeight: 1.6, wordBreak: 'break-word' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
        components={{
          pre: ({ children }) => {
            // 检查是否是代码块
            const isCodeBlock = React.Children.toArray(children).some(
              (child: any) => child?.type === 'code'
            );
            return isCodeBlock ? <>{children}</> : (
              <pre style={{
                background: '#f6f8fa', padding: 16, borderRadius: 6,
                overflowX: 'auto', margin: '12px 0', fontSize: 13, lineHeight: 1.5,
              }}>
                {children}
              </pre>
            );
          },
          code: CodeBlock,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer"
               style={{ color: '#1890ff', textDecoration: 'none' }}>
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote style={{
              borderLeft: '4px solid #d9d9d9', padding: '8px 16px',
              margin: '12px 0', color: '#666', background: '#fafafa',
            }}>
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <table style={{
              borderCollapse: 'collapse', margin: '12px 0', width: '100%',
            }}>
              {children}
            </table>
          ),
          th: ({ children }) => (
            <th style={{
              border: '1px solid #ddd', padding: '8px 12px', background: '#f6f8fa',
            }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{ border: '1px solid #ddd', padding: '8px 12px' }}>
              {children}
            </td>
          ),
          img: ({ src, alt }) => (
            <img src={src} alt={alt}
                 style={{ maxWidth: '100%', borderRadius: 4, margin: '8px 0' }} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
