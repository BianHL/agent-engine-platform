'use client';
import React, { useState } from 'react';
import { UserOutlined } from '@ant-design/icons';

interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: 'small' | 'medium' | 'large';
  shape?: 'circle' | 'square';
  'aria-label'?: string;
}

const sizeMap = {
  small: 32,
  medium: 40,
  large: 48,
};

const fontSizeMap = {
  small: 12,
  medium: 14,
  large: 16,
};

export default function Avatar({
  src,
  alt,
  name,
  size = 'medium',
  shape = 'circle',
  'aria-label': ariaLabel,
}: AvatarProps) {
  const [imgError, setImgError] = useState(false);
  const dimension = sizeMap[size];
  const fontSize = fontSizeMap[size];
  const borderRadius = shape === 'circle' ? '50%' : 'var(--ae-radius-md)';
  const label = ariaLabel || alt || name || 'User avatar';

  const getInitials = (fullName: string) => {
    const parts = fullName.trim().split(/\s+/);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return parts[0][0].toUpperCase();
  };

  const baseStyle: React.CSSProperties = {
    width: dimension,
    height: dimension,
    borderRadius,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--ae-accent-olive)',
    color: '#fff',
    fontSize,
    fontWeight: 600,
    overflow: 'hidden',
    flexShrink: 0,
  };

  if (src && !imgError) {
    return (
      <span aria-label={label} style={{ ...baseStyle, background: 'var(--ae-line)' }}>
        <img
          src={src}
          alt={alt || name || 'Avatar'}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          onError={() => setImgError(true)}
        />
      </span>
    );
  }

  if (name) {
    return (
      <span aria-label={label} style={baseStyle}>
        {getInitials(name)}
      </span>
    );
  }

  return (
    <span aria-label={label} style={baseStyle}>
      <UserOutlined style={{ fontSize: fontSize + 2 }} />
    </span>
  );
}
