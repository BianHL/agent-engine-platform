'use client';
import React, { useMemo } from 'react';
import { Dropdown, Badge, Tooltip, Button } from 'antd';
import {
  UserOutlined, LogoutOutlined, BellOutlined,
  MoonOutlined, SunOutlined, MenuOutlined, SearchOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/auth';
import { useTheme } from '@/components/ThemeProvider';

interface HeaderProps {
  onMenuClick?: () => void;
  onSearchClick?: () => void;
}

export default function Header({ onMenuClick, onSearchClick }: HeaderProps) {
  const { user, logout } = useAuthStore();
  const { mode, toggleMode } = useTheme();

  const items = useMemo(() => [
    { key: 'logout', icon: <LogoutOutlined />, label: 'Logout', onClick: logout },
  ], [logout]);

  const initials = user?.username
    ? user.username.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    <header
      style={{
        background: 'var(--ae-panel)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        padding: '0 28px',
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--ae-line)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        gap: 16,
      }}
    >
      {/* Left */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
        <Button
          type="text"
          icon={<MenuOutlined />}
          onClick={onMenuClick}
          className="md:hidden"
          style={{ color: 'var(--ae-muted)', width: 36, height: 36 }}
        />
        <button
          onClick={onSearchClick}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 14px', borderRadius: 18,
            border: '1px solid var(--ae-line)',
            background: 'rgba(255,255,255,0.50)',
            cursor: 'pointer', color: 'var(--ae-muted)',
            fontSize: 13, flex: 1, maxWidth: 400,
            transition: 'all 180ms ease',
          }}
        >
          <SearchOutlined />
          <span style={{ flex: 1, textAlign: 'left' }}>Search agents, workflows...</span>
          <kbd style={{ padding: '3px 8px', borderRadius: 8, background: 'rgba(255,255,255,0.72)', border: '1px solid var(--ae-line)', fontSize: 11 }}>⌘K</kbd>
        </button>
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Tooltip title="Notifications">
          <button className="header-action-btn" aria-label="Notifications">
            <Badge dot><BellOutlined /></Badge>
          </button>
        </Tooltip>
        <Tooltip title={mode === 'light' ? 'Dark mode' : 'Light mode'}>
          <button className="header-action-btn" onClick={toggleMode} aria-label={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
            {mode === 'light' ? <MoonOutlined /> : <SunOutlined />}
          </button>
        </Tooltip>
        <Dropdown menu={{ items }} placement="bottomRight">
          <div className="header-user">
            <div className="header-avatar">{initials}</div>
            <span className="header-username">{user?.username || 'User'}</span>
          </div>
        </Dropdown>
      </div>

      <style jsx>{`
        .header-action-btn {
          width: 36px; height: 36px;
          border-radius: 16px;
          border: 1px solid transparent;
          background: transparent;
          cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          color: var(--ae-muted);
          font-size: 16px;
          transition: all 180ms ease;
        }
        .header-action-btn:hover {
          background: rgba(255,255,255,0.50);
          color: var(--ae-text);
        }
        .header-user {
          display: flex; align-items: center; gap: 8px;
          cursor: pointer;
          padding: 4px 8px 4px 4px;
          border-radius: 16px;
          transition: all 180ms ease;
        }
        .header-user:hover {
          background: rgba(255,255,255,0.50);
        }
        .header-avatar {
          width: 32px; height: 32px;
          border-radius: 12px;
          background: linear-gradient(135deg, var(--ae-accent-olive), var(--ae-accent-gold));
          display: flex; align-items: center; justify-content: center;
          color: rgba(255,255,255,0.95); font-size: 12px; font-weight: 700;
        }
        .header-username {
          font-size: 13px; font-weight: 600;
          color: var(--ae-text);
          max-width: 100px;
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
      `}</style>
    </header>
  );
}
