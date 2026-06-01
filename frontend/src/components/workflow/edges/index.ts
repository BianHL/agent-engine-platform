import { lazy } from 'react';

export const edgeTypes = {
  custom: lazy(() => import('./CustomEdge').then((m) => ({ default: m.default }))),
};

// Re-export for convenience
export { default as CustomEdge } from './CustomEdge';
