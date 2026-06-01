'use client';
import React, { useMemo, useState } from 'react';
import { Drawer } from 'antd';
import {
  DashboardOutlined, RobotOutlined, DatabaseOutlined, SettingOutlined,
  BranchesOutlined, ToolOutlined, MessageOutlined, AuditOutlined,
  TeamOutlined, ExperimentOutlined, ThunderboltOutlined, ApiOutlined,
  ApartmentOutlined, SafetyOutlined, UserOutlined, ShopOutlined,
  FileOutlined, CheckCircleOutlined, BarChartOutlined, EyeOutlined,
  ImportOutlined, CodeOutlined, RocketOutlined, MenuFoldOutlined,
  DownOutlined, RightOutlined, KeyOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

interface MenuItemData {
  key: string;
  icon: React.ReactNode;
  label: string;
  count?: number;
  children?: MenuItemData[];
}

const menuItemsData: MenuItemData[] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/agents', icon: <RobotOutlined />, label: 'Agents', count: 12 },
  { key: '/knowledge', icon: <DatabaseOutlined />, label: 'Knowledge Base' },
  { key: '/workflows', icon: <BranchesOutlined />, label: 'Workflows' },
  { key: '/models', icon: <SettingOutlined />, label: 'Models' },
  { key: '/tools', icon: <ToolOutlined />, label: 'Tools' },
  { key: '/conversations', icon: <MessageOutlined />, label: 'Conversations', count: 5 },
  { key: '/audit', icon: <AuditOutlined />, label: 'Audit Logs' },
  { key: '/observability', icon: <EyeOutlined />, label: 'Observability' },
  { key: '/agent-versions', icon: <BranchesOutlined />, label: 'Versions & A/B' },
  { key: '/compliance', icon: <SafetyOutlined />, label: 'Compliance' },
  { key: '/plugins', icon: <ApiOutlined />, label: 'Plugins' },
  { key: '/import', icon: <ImportOutlined />, label: 'Data Import' },
  { key: '/prompt-editor', icon: <CodeOutlined />, label: 'Prompt Editor' },
  { key: '/publish', icon: <RocketOutlined />, label: 'Publish' },
  { key: '/model-compare', icon: <ExperimentOutlined />, label: 'Model Compare' },
  { key: '/variables', icon: <DatabaseOutlined />, label: 'Variables' },
  { key: '/tokens', icon: <KeyOutlined />, label: 'API Keys' },
];

const categoryItemsData: MenuItemData[] = [
  {
    key: 'marketplace',
    icon: <ShopOutlined />,
    label: 'Marketplace',
    children: [
      { key: '/marketplace', icon: <ShopOutlined />, label: 'Browse' },
      { key: '/marketplace/tools', icon: <ToolOutlined />, label: 'Tools' },
      { key: '/marketplace/my-submissions', icon: <FileOutlined />, label: 'My Submissions' },
      { key: '/marketplace/admin/reviews', icon: <CheckCircleOutlined />, label: 'Reviews' },
      { key: '/marketplace/admin/assets', icon: <SafetyOutlined />, label: 'Asset Control' },
      { key: '/marketplace/admin/dashboard', icon: <BarChartOutlined />, label: 'Operations' },
    ],
  },
  {
    key: 'multi-agent',
    icon: <TeamOutlined />,
    label: 'Multi-Agent',
    children: [
      { key: '/multi-agent', icon: <ApartmentOutlined />, label: 'Crews' },
    ],
  },
  {
    key: 'quality',
    icon: <ExperimentOutlined />,
    label: 'Quality',
    children: [
      { key: '/evaluations', icon: <ExperimentOutlined />, label: 'Evaluations' },
      { key: '/evaluations/playground', icon: <BarChartOutlined />, label: 'Playground' },
    ],
  },
  {
    key: 'automation',
    icon: <ThunderboltOutlined />,
    label: 'Automation',
    children: [
      { key: '/triggers', icon: <ThunderboltOutlined />, label: 'Triggers' },
      { key: '/webhooks', icon: <ApiOutlined />, label: 'Webhooks' },
    ],
  },
  {
    key: 'admin',
    icon: <SafetyOutlined />,
    label: 'Admin',
    children: [
      { key: '/tenants', icon: <ApartmentOutlined />, label: 'Tenants' },
      { key: '/roles', icon: <SafetyOutlined />, label: 'Roles' },
      { key: '/users', icon: <UserOutlined />, label: 'Users' },
    ],
  },
];

function NavItem({
  item,
  isActive,
  onClick,
  depth = 0,
}: {
  item: MenuItemData;
  isActive: boolean;
  onClick: (key: string) => void;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const pathname = usePathname();
  const hasChildren = item.children && item.children.length > 0;
  const active = isActive || (hasChildren && item.children?.some(c => c.key === pathname));

  if (hasChildren) {
    return (
      <div style={{ marginBottom: 4 }}>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 14px',
            borderRadius: 'var(--ae-radius-md)',
            border: 'none',
            background: expanded ? 'rgba(255,255,255,0.52)' : 'transparent',
            cursor: 'pointer',
            color: 'var(--ae-text)',
            fontSize: 14,
            fontWeight: 500,
            transition: 'all 180ms ease',
            textAlign: 'left',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.52)';
            e.currentTarget.style.transform = 'translateX(2px)';
          }}
          onMouseLeave={(e) => {
            if (!expanded) {
              e.currentTarget.style.background = 'transparent';
            }
            e.currentTarget.style.transform = 'translateX(0)';
          }}
        >
          <span
            style={{
              width: 22,
              height: 22,
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(122, 138, 106, 0.12)',
              color: 'var(--ae-accent-olive)',
              fontSize: 12,
              flexShrink: 0,
            }}
          >
            {item.icon}
          </span>
          <span style={{ flex: 1 }}>{item.label}</span>
          <span
            style={{
              fontSize: 10,
              color: 'var(--ae-muted)',
              transition: 'transform 180ms ease',
              transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
            }}
          >
            <RightOutlined />
          </span>
        </button>
        {expanded && (
          <div style={{ paddingLeft: 8, marginTop: 4 }}>
            {item.children?.map((child) => (
              <NavItem
                key={child.key}
                item={child}
                isActive={pathname === child.key}
                onClick={onClick}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => onClick(item.key)}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 14px',
        borderRadius: 'var(--ae-radius-md)',
        border: 'none',
        background: isActive
          ? 'rgba(255,255,255,0.72)'
          : 'rgba(255,255,255,0.52)',
        cursor: 'pointer',
        color: 'var(--ae-text)',
        fontSize: 14,
        fontWeight: isActive ? 600 : 500,
        transition: 'all 180ms ease',
        textAlign: 'left',
        position: 'relative',
        boxShadow: isActive
          ? '0 2px 8px rgba(74, 60, 48, 0.08)'
          : 'none',
        marginBottom: 4,
        paddingLeft: isActive ? '11px' : '14px',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(255,255,255,0.72)';
        e.currentTarget.style.transform = 'translateX(2px)';
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(74, 60, 48, 0.08)';
      }}
      onMouseLeave={(e) => {
        if (!isActive) {
          e.currentTarget.style.background = 'rgba(255,255,255,0.52)';
          e.currentTarget.style.boxShadow = 'none';
        }
        e.currentTarget.style.transform = 'translateX(0)';
      }}
    >
      {isActive && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: '50%',
            transform: 'translateY(-50%)',
            width: 3,
            height: 20,
            borderRadius: '0 2px 2px 0',
            background: 'linear-gradient(180deg, var(--ae-accent-olive), var(--ae-accent-gold))',
          }}
        />
      )}
      <span
        style={{
          width: 22,
          height: 22,
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: isActive
            ? 'rgba(122, 138, 106, 0.18)'
            : 'rgba(122, 138, 106, 0.12)',
          color: isActive ? 'var(--ae-accent-olive)' : 'var(--ae-muted)',
          fontSize: 12,
          flexShrink: 0,
          transition: 'all 180ms ease',
        }}
      >
        {item.icon}
      </span>
      <span style={{ flex: 1 }}>{item.label}</span>
      {item.count !== undefined && item.count > 0 && (
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--ae-muted)',
            background: 'rgba(255,255,255,0.6)',
            padding: '2px 8px',
            borderRadius: 'var(--ae-radius-full)',
            minWidth: 22,
            textAlign: 'center',
          }}
        >
          {item.count}
        </span>
      )}
    </button>
  );
}

function SidebarContent({ onItemClick }: { onItemClick: (key: string) => void }) {
  const pathname = usePathname();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        padding: '28px 20px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative radial gradient */}
      <div
        style={{
          position: 'absolute',
          bottom: -60,
          right: -60,
          width: 240,
          height: 240,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(194, 154, 99, 0.15), transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Brand Logo */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '0 4px 20px',
          marginBottom: 8,
          borderBottom: '1px solid var(--ae-line)',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 'var(--ae-radius-md)',
            background: 'linear-gradient(135deg, var(--ae-accent-olive), var(--ae-accent-gold))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'rgba(255,255,255,0.95)',
            fontSize: 18,
            fontWeight: 700,
            flexShrink: 0,
            boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.3), 0 4px 12px rgba(122, 138, 106, 0.25)',
            fontFamily: 'var(--ae-font-family-serif)',
          }}
        >
          AE
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span
            style={{
              fontWeight: 700,
              fontSize: 17,
              color: 'var(--ae-text)',
              letterSpacing: '-0.02em',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              fontFamily: 'var(--ae-font-family-serif)',
              lineHeight: 1.2,
            }}
          >
            Agent Engine
          </span>
          <span
            style={{
              fontSize: 11,
              color: 'var(--ae-muted)',
              fontWeight: 400,
              letterSpacing: '0.02em',
              whiteSpace: 'nowrap',
            }}
          >
            Design Lab · soft editorial UI
          </span>
        </div>
      </div>

      {/* Navigation */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          position: 'relative',
          zIndex: 1,
          padding: '4px 0',
        }}
      >
        {/* Main nav items */}
        <div style={{ marginBottom: 12 }}>
          {menuItemsData.map((item) => (
            <NavItem
              key={item.key}
              item={item}
              isActive={pathname === item.key}
              onClick={onItemClick}
            />
          ))}
        </div>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: 'var(--ae-line)',
            margin: '12px 4px',
          }}
        />

        {/* Category items */}
        <div>
          {categoryItemsData.map((item) => (
            <NavItem
              key={item.key}
              item={item}
              isActive={pathname === item.key}
              onClick={onItemClick}
            />
          ))}
        </div>
      </div>

      {/* Cards Section */}
      <div
        style={{
          position: 'relative',
          zIndex: 1,
          marginTop: 'auto',
          paddingTop: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {/* System Tags Card */}
        <div
          style={{
            background: 'var(--ae-panel)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            borderRadius: 'var(--ae-radius-lg)',
            padding: '14px 16px',
            border: '1px solid var(--ae-line)',
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--ae-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: 10,
            }}
          >
            System
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {['v2.4', 'stable', 'pro'].map((tag) => (
              <span
                key={tag}
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  padding: '4px 10px',
                  borderRadius: 'var(--ae-radius-full)',
                  background: 'rgba(122, 138, 106, 0.10)',
                  color: 'var(--ae-accent-olive)',
                  border: '1px solid rgba(122, 138, 106, 0.15)',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Design Intent Card */}
        <div
          style={{
            background: 'var(--ae-panel)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            borderRadius: 'var(--ae-radius-lg)',
            padding: '14px 16px',
            border: '1px solid var(--ae-line)',
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--ae-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: 6,
            }}
          >
            Design Intent
          </div>
          <p
            style={{
              fontSize: 12,
              lineHeight: 1.5,
              color: 'var(--ae-muted)',
              margin: 0,
            }}
          >
            Warm editorial aesthetic with glassmorphism panels and olive accents.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const router = useRouter();

  const handleItemClick = (key: string) => {
    const nonNavigable = ['multi-agent', 'quality', 'automation', 'admin', 'marketplace'];
    if (!nonNavigable.includes(key)) {
      router.push(key);
      onMobileClose?.();
    }
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        style={{
          width: 'var(--ae-sidebar-width)',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          background: 'rgba(245, 239, 230, 0.72)',
          backdropFilter: 'blur(18px)',
          WebkitBackdropFilter: 'blur(18px)',
          borderRight: '1px solid var(--ae-line)',
        }}
        className="hidden md:block"
      >
        <SidebarContent onItemClick={handleItemClick} />
      </aside>

      {/* Mobile Drawer */}
      <Drawer
        placement="left"
        closable={false}
        onClose={onMobileClose}
        open={mobileOpen}
        width={280}
        bodyStyle={{ padding: 0, background: 'rgba(245, 239, 230, 0.92)' }}
        maskStyle={{ background: 'var(--ae-overlay)' }}
      >
        <SidebarContent onItemClick={handleItemClick} />
      </Drawer>
    </>
  );
}
