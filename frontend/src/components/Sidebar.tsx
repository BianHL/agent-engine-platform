'use client';
import React, { useState } from 'react';
import { Drawer } from 'antd';
import {
  DashboardOutlined, RobotOutlined, DatabaseOutlined, SettingOutlined,
  BranchesOutlined, ToolOutlined, MessageOutlined, AuditOutlined,
  TeamOutlined, ExperimentOutlined, ThunderboltOutlined, ApiOutlined,
  ApartmentOutlined, SafetyOutlined, UserOutlined, ShopOutlined,
  FileOutlined, CheckCircleOutlined, BarChartOutlined, EyeOutlined,
  ImportOutlined, CodeOutlined, RocketOutlined, RightOutlined, KeyOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

interface MenuChild {
  key: string;
  label: string;
}

interface MenuGroup {
  key: string;
  icon: React.ReactNode;
  label: string;
  route?: string;
  children?: MenuChild[];
}

const menuData: MenuGroup[] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard', route: '/dashboard' },
  {
    key: 'agents',
    icon: <RobotOutlined />,
    label: 'Agents',
    children: [
      { key: '/agents', label: 'Agents' },
      { key: '/conversations', label: 'Conversations' },
      { key: '/knowledge', label: 'Knowledge Base' },
      { key: '/tools', label: 'Tools' },
      { key: '/prompt-editor', label: 'Prompt Editor' },
      { key: '/publish', label: 'Publish' },
    ],
  },
  {
    key: 'orchestration',
    icon: <BranchesOutlined />,
    label: 'Orchestration',
    children: [
      { key: '/workflows', label: 'Workflows' },
      { key: '/multi-agent', label: 'Multi-Agent' },
      { key: '/triggers', label: 'Triggers' },
      { key: '/webhooks', label: 'Webhooks' },
    ],
  },
  {
    key: 'models',
    icon: <SettingOutlined />,
    label: 'Models',
    children: [
      { key: '/models', label: 'Models' },
      { key: '/model-compare', label: 'Model Compare' },
      { key: '/variables', label: 'Variables' },
      { key: '/evaluations', label: 'Evaluations' },
      { key: '/evaluations/playground', label: 'Playground' },
    ],
  },
  {
    key: 'marketplace',
    icon: <ShopOutlined />,
    label: 'Marketplace',
    children: [
      { key: '/marketplace', label: 'Browse' },
      { key: '/marketplace/tools', label: 'Tools' },
      { key: '/marketplace/my-submissions', label: 'My Submissions' },
      { key: '/marketplace/admin/reviews', label: 'Reviews' },
      { key: '/marketplace/admin/assets', label: 'Asset Control' },
      { key: '/marketplace/admin/dashboard', label: 'Operations' },
    ],
  },
  {
    key: 'observability',
    icon: <EyeOutlined />,
    label: 'Observability',
    children: [
      { key: '/audit', label: 'Audit Logs' },
      { key: '/observability', label: 'Observability' },
      { key: '/compliance', label: 'Compliance' },
      { key: '/agent-versions', label: 'Versions & A/B' },
    ],
  },
  {
    key: 'system',
    icon: <SafetyOutlined />,
    label: 'System',
    children: [
      { key: '/tokens', label: 'API Keys' },
      { key: '/plugins', label: 'Plugins' },
      { key: '/import', label: 'Data Import' },
      { key: '/tenants', label: 'Tenants' },
      { key: '/roles', label: 'Roles' },
      { key: '/users', label: 'Users' },
    ],
  },
];

function NavItem({
  item,
  isActive,
  onClick,
  depth = 0,
}: {
  item: MenuGroup;
  isActive: boolean;
  onClick: (key: string) => void;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const pathname = usePathname();
  const hasChildren = item.children && item.children.length > 0;
  const active = isActive || (hasChildren && item.children?.some((c) => c.key === pathname));

  const isChild = depth > 0;

  if (hasChildren) {
    return (
      <div style={{ marginBottom: 4 }}>
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: isChild ? '8px 14px 8px 24px' : '10px 14px',
            borderRadius: 'var(--ae-radius-md)',
            border: 'none',
            background: expanded || active ? 'rgba(255,255,255,0.52)' : 'transparent',
            cursor: 'pointer',
            color: 'var(--ae-text)',
            fontSize: isChild ? 13 : 14,
            fontWeight: 500,
            transition: 'all 180ms ease',
            textAlign: 'left',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.52)';
            if (!isChild) e.currentTarget.style.transform = 'translateX(2px)';
          }}
          onMouseLeave={(e) => {
            if (!expanded && !active) {
              e.currentTarget.style.background = 'transparent';
            }
            if (!isChild) e.currentTarget.style.transform = 'translateX(0)';
          }}
        >
          {!isChild && (
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: active
                  ? 'rgba(122, 138, 106, 0.18)'
                  : 'rgba(122, 138, 106, 0.12)',
                color: active ? 'var(--ae-accent-olive)' : 'var(--ae-accent-olive)',
                fontSize: 12,
                flexShrink: 0,
              }}
            >
              {item.icon}
            </span>
          )}
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
          <div style={{ paddingLeft: 0, marginTop: 2 }}>
            {item.children?.map((child) => (
              <NavItem
                key={child.key}
                item={{ key: child.key, icon: null, label: child.label, route: child.key }}
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
      type="button"
      aria-current={isActive ? 'page' : undefined}
      onClick={() => onClick(item.key)}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: isChild ? '8px 14px 8px 24px' : '10px 14px',
        borderRadius: 'var(--ae-radius-md)',
        border: 'none',
        background: isActive
          ? 'rgba(255,255,255,0.72)'
          : isChild
            ? 'transparent'
            : 'rgba(255,255,255,0.52)',
        cursor: 'pointer',
        color: 'var(--ae-text)',
        fontSize: isChild ? 13 : 14,
        fontWeight: isActive ? 600 : 500,
        transition: 'all 180ms ease',
        textAlign: 'left',
        position: 'relative',
        boxShadow: isActive && !isChild
          ? '0 2px 8px rgba(74, 60, 48, 0.08)'
          : 'none',
        marginBottom: 2,
        paddingLeft: isActive && !isChild ? '11px' : isChild ? '24px' : '14px',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(255,255,255,0.72)';
        if (!isChild) {
          e.currentTarget.style.transform = 'translateX(2px)';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(74, 60, 48, 0.08)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isActive) {
          e.currentTarget.style.background = isChild ? 'transparent' : 'rgba(255,255,255,0.52)';
          e.currentTarget.style.boxShadow = 'none';
        }
        if (!isChild) e.currentTarget.style.transform = 'translateX(0)';
      }}
    >
      {isActive && !isChild && (
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
      {!isChild && item.icon && (
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
      )}
      <span style={{ flex: 1 }}>{item.label}</span>
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
      <nav
        aria-label="Main navigation"
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          position: 'relative',
          zIndex: 1,
          padding: '4px 0',
        }}
      >
        {menuData.map((item) => (
          <NavItem
            key={item.key}
            item={item}
            isActive={pathname === item.key}
            onClick={onItemClick}
          />
        ))}
      </nav>

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
    const group = menuData.find((m) => m.key === key);
    if (group?.route) {
      router.push(group.route);
      onMobileClose?.();
    }
    const childRoute = menuData.flatMap((m) => m.children || []).find((c) => c.key === key);
    if (childRoute) {
      router.push(childRoute.key);
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
