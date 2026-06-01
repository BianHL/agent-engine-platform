import { create } from 'zustand';
import { temporal } from 'zundo';
import type { WorkflowNode, WorkflowEdge, NodeExecutionStatus } from '@/types';

interface WorkflowState {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selectedNodeId: string | null;
  nodeExecutionStatus: Record<string, NodeExecutionStatus>;
  isExecuting: boolean;
  viewport: { x: number; y: number; zoom: number };

  // Actions
  setNodes: (nodes: WorkflowNode[] | ((prev: WorkflowNode[]) => WorkflowNode[])) => void;
  setEdges: (edges: WorkflowEdge[] | ((prev: WorkflowEdge[]) => WorkflowEdge[])) => void;
  addNode: (node: WorkflowNode) => void;
  updateNode: (id: string, updates: Partial<WorkflowNode>) => void;
  deleteNode: (id: string) => void;
  addEdge: (edge: WorkflowEdge) => void;
  deleteEdge: (id: string) => void;
  setSelectedNode: (id: string | null) => void;
  setNodeExecutionStatus: (nodeId: string, status: NodeExecutionStatus) => void;
  clearExecutionStatus: () => void;
  setIsExecuting: (isExecuting: boolean) => void;
  setViewport: (viewport: { x: number; y: number; zoom: number }) => void;
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowState>()(
  temporal<WorkflowState>((set) => ({
    nodes: [],
    edges: [],
    selectedNodeId: null,
    nodeExecutionStatus: {},
    isExecuting: false,
    viewport: { x: 0, y: 0, zoom: 1 },

    setNodes: (nodes) =>
      set((state) => ({
        nodes: typeof nodes === 'function' ? nodes(state.nodes) : nodes,
      })),

    setEdges: (edges) =>
      set((state) => ({
        edges: typeof edges === 'function' ? edges(state.edges) : edges,
      })),

    addNode: (node) =>
      set((state) => ({
        nodes: [...state.nodes, node],
      })),

    updateNode: (id, updates) =>
      set((state) => ({
        nodes: state.nodes.map((node) =>
          node.id === id ? { ...node, ...updates } : node
        ),
      })),

    deleteNode: (id) =>
      set((state) => ({
        nodes: state.nodes.filter((node) => node.id !== id),
        edges: state.edges.filter(
          (edge) => edge.source !== id && edge.target !== id
        ),
        selectedNodeId:
          state.selectedNodeId === id ? null : state.selectedNodeId,
      })),

    addEdge: (edge) =>
      set((state) => {
        const exists = state.edges.some(
          (e) => e.source === edge.source && e.target === edge.target
        );
        if (exists) return state;
        return { edges: [...state.edges, edge] };
      }),

    deleteEdge: (id) =>
      set((state) => ({
        edges: state.edges.filter((edge) => edge.id !== id),
      })),

    setSelectedNode: (id) => set({ selectedNodeId: id }),

    setNodeExecutionStatus: (nodeId, status) =>
      set((state) => ({
        nodeExecutionStatus: {
          ...state.nodeExecutionStatus,
          [nodeId]: status,
        },
      })),

    clearExecutionStatus: () =>
      set({ nodeExecutionStatus: {}, isExecuting: false }),

    setIsExecuting: (isExecuting) => set({ isExecuting }),

    setViewport: (viewport) => set({ viewport }),

    reset: () => ({
      nodes: [],
      edges: [],
      selectedNodeId: null,
      nodeExecutionStatus: {},
      isExecuting: false,
      viewport: { x: 0, y: 0, zoom: 1 },
    }),
  }))
);

// Selector hooks for better performance
export const useNodes = () => useWorkflowStore((state) => state.nodes);
export const useEdges = () => useWorkflowStore((state) => state.edges);
export const useSelectedNode = () =>
  useWorkflowStore((state) =>
    state.nodes.find((n) => n.id === state.selectedNodeId) || null
  );
export const useNodeExecutionStatus = () =>
  useWorkflowStore((state) => state.nodeExecutionStatus);
