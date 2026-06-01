import { act } from '@testing-library/react';

// Mock zundo's temporal to just pass through the state creator
jest.mock('zundo', () => ({
  temporal: <T>(creator: any) => creator,
}));

import { useWorkflowStore } from '../workflow-store';
import type { WorkflowNode, WorkflowEdge, NodeExecutionStatus } from '@/types';

const makeNode = (id: string, overrides?: Partial<WorkflowNode>): WorkflowNode => ({
  id,
  type: 'llm',
  label: `Node ${id}`,
  config: {},
  position: { x: 0, y: 0 },
  ...overrides,
});

const makeEdge = (id: string, source: string, target: string, overrides?: Partial<WorkflowEdge>): WorkflowEdge => ({
  id,
  source,
  target,
  ...overrides,
});

describe('WorkflowStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    useWorkflowStore.setState({
      nodes: [],
      edges: [],
      selectedNodeId: null,
      nodeExecutionStatus: {},
      isExecuting: false,
      viewport: { x: 0, y: 0, zoom: 1 },
    });
  });

  describe('setNodes', () => {
    it('sets nodes directly', () => {
      const nodes = [makeNode('a'), makeNode('b')];
      act(() => useWorkflowStore.getState().setNodes(nodes));
      expect(useWorkflowStore.getState().nodes).toEqual(nodes);
    });

    it('sets nodes via updater function', () => {
      act(() => useWorkflowStore.getState().addNode(makeNode('a')));
      act(() => useWorkflowStore.getState().setNodes((prev) => [...prev, makeNode('b')]));
      expect(useWorkflowStore.getState().nodes).toHaveLength(2);
    });
  });

  describe('setEdges', () => {
    it('sets edges directly', () => {
      const edges = [makeEdge('e1', 'a', 'b')];
      act(() => useWorkflowStore.getState().setEdges(edges));
      expect(useWorkflowStore.getState().edges).toEqual(edges);
    });

    it('sets edges via updater function', () => {
      act(() => useWorkflowStore.getState().setEdges((prev) => [...prev, makeEdge('e1', 'a', 'b')]));
      expect(useWorkflowStore.getState().edges).toHaveLength(1);
    });
  });

  describe('addNode', () => {
    it('appends a node to the list', () => {
      act(() => useWorkflowStore.getState().addNode(makeNode('a')));
      act(() => useWorkflowStore.getState().addNode(makeNode('b')));
      expect(useWorkflowStore.getState().nodes).toHaveLength(2);
      expect(useWorkflowStore.getState().nodes.map((n) => n.id)).toEqual(['a', 'b']);
    });
  });

  describe('updateNode', () => {
    it('updates matching node fields', () => {
      act(() => useWorkflowStore.getState().addNode(makeNode('a', { label: 'Old' })));
      act(() => useWorkflowStore.getState().updateNode('a', { label: 'New' }));
      expect(useWorkflowStore.getState().nodes[0].label).toBe('New');
    });

    it('does not modify non-matching nodes', () => {
      act(() => useWorkflowStore.getState().addNode(makeNode('a')));
      act(() => useWorkflowStore.getState().addNode(makeNode('b')));
      act(() => useWorkflowStore.getState().updateNode('a', { label: 'Changed' }));
      expect(useWorkflowStore.getState().nodes[1].label).toBe('Node b');
    });
  });

  describe('deleteNode', () => {
    it('removes the node by id', () => {
      act(() => useWorkflowStore.getState().addNode(makeNode('a')));
      act(() => useWorkflowStore.getState().addNode(makeNode('b')));
      act(() => useWorkflowStore.getState().deleteNode('a'));
      expect(useWorkflowStore.getState().nodes).toHaveLength(1);
      expect(useWorkflowStore.getState().nodes[0].id).toBe('b');
    });

    it('removes edges connected to the deleted node', () => {
      act(() => {
        const s = useWorkflowStore.getState();
        s.addNode(makeNode('a'));
        s.addNode(makeNode('b'));
        s.addNode(makeNode('c'));
        s.addEdge(makeEdge('e1', 'a', 'b'));
        s.addEdge(makeEdge('e2', 'b', 'c'));
      });
      act(() => useWorkflowStore.getState().deleteNode('b'));
      expect(useWorkflowStore.getState().edges).toHaveLength(0);
    });

    it('clears selectedNodeId if deleted node was selected', () => {
      act(() => {
        useWorkflowStore.getState().addNode(makeNode('a'));
        useWorkflowStore.getState().setSelectedNode('a');
      });
      act(() => useWorkflowStore.getState().deleteNode('a'));
      expect(useWorkflowStore.getState().selectedNodeId).toBeNull();
    });

    it('keeps selectedNodeId if deleted node was not selected', () => {
      act(() => {
        useWorkflowStore.getState().addNode(makeNode('a'));
        useWorkflowStore.getState().addNode(makeNode('b'));
        useWorkflowStore.getState().setSelectedNode('a');
      });
      act(() => useWorkflowStore.getState().deleteNode('b'));
      expect(useWorkflowStore.getState().selectedNodeId).toBe('a');
    });
  });

  describe('addEdge', () => {
    it('appends an edge', () => {
      act(() => useWorkflowStore.getState().addEdge(makeEdge('e1', 'a', 'b')));
      expect(useWorkflowStore.getState().edges).toHaveLength(1);
    });

    it('prevents duplicate edges (same source and target)', () => {
      act(() => {
        useWorkflowStore.getState().addEdge(makeEdge('e1', 'a', 'b'));
        useWorkflowStore.getState().addEdge(makeEdge('e2', 'a', 'b'));
      });
      expect(useWorkflowStore.getState().edges).toHaveLength(1);
    });

    it('allows edges with same source but different target', () => {
      act(() => {
        useWorkflowStore.getState().addEdge(makeEdge('e1', 'a', 'b'));
        useWorkflowStore.getState().addEdge(makeEdge('e2', 'a', 'c'));
      });
      expect(useWorkflowStore.getState().edges).toHaveLength(2);
    });
  });

  describe('deleteEdge', () => {
    it('removes the edge by id', () => {
      act(() => {
        useWorkflowStore.getState().addEdge(makeEdge('e1', 'a', 'b'));
        useWorkflowStore.getState().addEdge(makeEdge('e2', 'b', 'c'));
      });
      act(() => useWorkflowStore.getState().deleteEdge('e1'));
      expect(useWorkflowStore.getState().edges).toHaveLength(1);
      expect(useWorkflowStore.getState().edges[0].id).toBe('e2');
    });
  });

  describe('setSelectedNode', () => {
    it('sets the selected node id', () => {
      act(() => useWorkflowStore.getState().setSelectedNode('node-1'));
      expect(useWorkflowStore.getState().selectedNodeId).toBe('node-1');
    });

    it('clears selection with null', () => {
      act(() => useWorkflowStore.getState().setSelectedNode('node-1'));
      act(() => useWorkflowStore.getState().setSelectedNode(null));
      expect(useWorkflowStore.getState().selectedNodeId).toBeNull();
    });
  });

  describe('setNodeExecutionStatus', () => {
    it('sets execution status for a node', () => {
      const status: NodeExecutionStatus = { node_id: 'a', status: 'running' };
      act(() => useWorkflowStore.getState().setNodeExecutionStatus('a', status));
      expect(useWorkflowStore.getState().nodeExecutionStatus['a']).toEqual(status);
    });

    it('updates execution status independently per node', () => {
      act(() => {
        useWorkflowStore.getState().setNodeExecutionStatus('a', { node_id: 'a', status: 'completed' });
        useWorkflowStore.getState().setNodeExecutionStatus('b', { node_id: 'b', status: 'running' });
      });
      const status = useWorkflowStore.getState().nodeExecutionStatus;
      expect(status['a'].status).toBe('completed');
      expect(status['b'].status).toBe('running');
    });
  });

  describe('clearExecutionStatus', () => {
    it('clears all execution statuses and resets isExecuting', () => {
      act(() => {
        useWorkflowStore.getState().setNodeExecutionStatus('a', { node_id: 'a', status: 'running' });
        useWorkflowStore.getState().setIsExecuting(true);
      });
      act(() => useWorkflowStore.getState().clearExecutionStatus());
      expect(useWorkflowStore.getState().nodeExecutionStatus).toEqual({});
      expect(useWorkflowStore.getState().isExecuting).toBe(false);
    });
  });

  describe('setIsExecuting', () => {
    it('toggles isExecuting', () => {
      act(() => useWorkflowStore.getState().setIsExecuting(true));
      expect(useWorkflowStore.getState().isExecuting).toBe(true);
      act(() => useWorkflowStore.getState().setIsExecuting(false));
      expect(useWorkflowStore.getState().isExecuting).toBe(false);
    });
  });

  describe('setViewport', () => {
    it('updates viewport', () => {
      act(() => useWorkflowStore.getState().setViewport({ x: 100, y: 200, zoom: 1.5 }));
      expect(useWorkflowStore.getState().viewport).toEqual({ x: 100, y: 200, zoom: 1.5 });
    });
  });

  describe('reset', () => {
    it('resets all state to initial values', () => {
      act(() => {
        const s = useWorkflowStore.getState();
        s.addNode(makeNode('a'));
        s.addEdge(makeEdge('e1', 'a', 'b'));
        s.setSelectedNode('a');
        s.setIsExecuting(true);
        s.setViewport({ x: 50, y: 50, zoom: 2 });
      });

      const result = useWorkflowStore.getState().reset();
      // reset returns the new state but does not call set — it's used as the state setter
      expect(result).toEqual({
        nodes: [],
        edges: [],
        selectedNodeId: null,
        nodeExecutionStatus: {},
        isExecuting: false,
        viewport: { x: 0, y: 0, zoom: 1 },
      });
    });
  });
});
