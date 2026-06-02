'use client';
import React from 'react';
import { usePathname } from 'next/navigation';
import { HomeOutlined } from '@ant-design/icons';

const pathNameMap: Record<string, string> = {
  dashboard: 'Dashboard',
  agents: 'Agents',
  knowledge: 'Knowledge Base',
  workflows: 'Workflows',
  models: 'Models',
  tools: 'Tools',
  conversations: 'Conversations',
  audit: 'Audit Logs',
  observability: 'Observability',
  marketplace: 'Marketplace',
  'my-submissions': 'My Submissions',
  admin: 'Admin',
  reviews: 'Reviews',
  assets: 'Asset Control',
  dashboard2: 'Operations',
  'multi-agent': 'Multi-Agent',
  crews: 'Crews',
  evaluations: 'Evaluations',
  playground: 'Playground',
  triggers: 'Triggers',
  webhooks: 'Webhooks',
  tenants: 'Tenants',
  roles: 'Roles',
  users: 'Users',
  compliance: 'Compliance',
  plugins: 'Plugins',
  import: 'Data Import',
  'prompt-editor': 'Prompt Editor',
  publish: 'Publish',
  'model-compare': 'Model Compare',
  variables: 'Variables',
  tokens: 'API Keys',
  'agent-versions': 'Versions & A/B',
  create: 'Create',
  edit: 'Edit',
  chat: 'Chat',
};

function segmentToLabel(segment: string): string {
  if (pathNameMap[segment]) return pathNameMap[segment];
  // Dynamic IDs (uuids, numbers)
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment)) return 'Detail';
  if (/^\d+$/.test(segment)) return 'Detail';
  // Fallback: capitalize and replace hyphens
  return segment
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export default function BreadcrumbNav() {
  const pathname = usePathname();
  if (!pathname || pathname === '/dashboard') return null;

  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return null;

  const crumbs = segments.map((segment, index) => {
    const href = '/' + segments.slice(0, index + 1).join('/');
    const isLast = index === segments.length - 1;
    return { label: segmentToLabel(segment), href, isLast };
  });

  return (
    <nav aria-label="Breadcrumb">
      <ol
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          listStyle: 'none',
          margin: 0,
          padding: '0 0 12px',
          fontSize: 13,
          color: 'var(--ae-muted)',
        }}
      >
        <li>
          <a
            href="/dashboard"
            style={{ color: 'var(--ae-muted)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <HomeOutlined style={{ fontSize: 12 }} />
          </a>
        </li>
        {crumbs.map((crumb, i) => (
          <React.Fragment key={crumb.href}>
            <li aria-hidden="true" style={{ color: 'var(--ae-line-strong)' }}>/</li>
            <li>
              {crumb.isLast ? (
                <span aria-current="page" style={{ color: 'var(--ae-text)', fontWeight: 500 }}>
                  {crumb.label}
                </span>
              ) : (
                <a href={crumb.href} style={{ color: 'var(--ae-muted)', textDecoration: 'none' }}>
                  {crumb.label}
                </a>
              )}
            </li>
          </React.Fragment>
        ))}
      </ol>
    </nav>
  );
}
