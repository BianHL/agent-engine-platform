import { lazy } from 'react';
import type { WorkflowNode } from '@/types';

export const nodeTypes = {
  llm: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  code: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  condition: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  parallel: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  loop: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  http: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  human: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
  sub_workflow: lazy(() =>
    import('./BaseNode').then((m) => ({ default: m.default }))
  ),
};

// Re-export for convenience
export { default as BaseNode } from './BaseNode';
export * from './nodeTypes';
