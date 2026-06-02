export interface User {
  id: string;
  username: string;
  role: string;
  tenant_id: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  model_provider: string;
  model_name: string;
  system_prompt: string;
  tools: string[];
  knowledge_base_ids: string[];
  status: 'draft' | 'published';
  version: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  embedding_model: string;
  document_count: number;
  status: string;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  task_id?: string;
  created_at: string;
}

export interface Chunk {
  id: string;
  document_id: string;
  content: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

export interface RetrievalResult {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface ToolCall {
  function?: {
    name: string;
    arguments?: string;
  };
  output?: string;
  status?: 'running' | 'completed' | 'failed';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  agent_name?: string;
  status?: 'running' | 'completed' | 'failed';
  tool_calls?: ToolCall[];
}

export interface Conversation {
  id: string;
  agent_id: string;
  title: string;
  status?: string;
  created_at: string;
  updated_at?: string;
}

export interface ModelProvider {
  id: string;
  name: string;
  provider_type: string;
  status: string;
}

export interface ModelConfig {
  id: string;
  provider_id: string;
  model_name: string;
  model_type: string;
  display_name: string;
  is_default: boolean;
  enabled: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user_id: string;
  ip_address?: string;
  detail?: Record<string, unknown>;
  before_data?: Record<string, unknown>;
  after_data?: Record<string, unknown>;
  created_at: string;
}

// Workflow Types
export type NodeType = 'llm' | 'code' | 'condition' | 'parallel' | 'loop' | 'http' | 'human' | 'sub_workflow';

export interface WorkflowNodeData extends Record<string, unknown> {
  id: string;
  type: NodeType;
  label: string;
  config: Record<string, unknown>;
  position?: { x: number; y: number };
  style?: React.CSSProperties;
}

export interface WorkflowNode extends WorkflowNodeData {
  id: string;
  type: NodeType;
  label: string;
  config: Record<string, unknown>;
  position: { x: number; y: number };
  style?: React.CSSProperties;
}

export interface WorkflowEdge extends Record<string, unknown> {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: React.ReactNode;
  style?: React.CSSProperties;
  animated?: boolean;
  data?: Record<string, unknown>;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'published';
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface NodeExecutionStatus {
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  result?: unknown;
  error?: string;
}
