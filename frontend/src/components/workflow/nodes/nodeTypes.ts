import type { WorkflowNode } from '@/types';

export const NODE_TYPES = [
  {
    type: 'llm' as const,
    label: 'LLM',
    color: '#1890ff',
    icon: '🤖',
    description: 'Large Language Model inference node',
  },
  {
    type: 'code' as const,
    label: 'Code',
    color: '#eb2f96',
    icon: '⚡',
    description: 'Execute custom code',
  },
  {
    type: 'condition' as const,
    label: 'Condition',
    color: '#faad14',
    icon: '🔀',
    description: 'Conditional branching',
  },
  {
    type: 'parallel' as const,
    label: 'Parallel',
    color: '#52c41a',
    icon: '⚙️',
    description: 'Execute nodes in parallel',
  },
  {
    type: 'loop' as const,
    label: 'Loop',
    color: '#722ed1',
    icon: '🔄',
    description: 'Iterative execution',
  },
  {
    type: 'http' as const,
    label: 'HTTP',
    color: '#13c2c2',
    icon: '🌐',
    description: 'HTTP request',
  },
  {
    type: 'human' as const,
    label: 'Human',
    color: '#fa541c',
    icon: '👤',
    description: 'Human in the loop',
  },
  {
    type: 'sub_workflow' as const,
    label: 'Sub Workflow',
    color: '#2f54eb',
    icon: '📋',
    description: 'Nested workflow',
  },
];

export const getNodeTypeConfig = (type: WorkflowNode['type']) => {
  return NODE_TYPES.find((t) => t.type === type) || NODE_TYPES[0];
};

export const createDefaultNode = (
  type: WorkflowNode['type'],
  position: { x: number; y: number }
): WorkflowNode => {
  const config = getNodeTypeConfig(type);
  return {
    id: `${type}_${Date.now()}`,
    type,
    label: config.label,
    config: getDefaultConfigForType(type) as Record<string, unknown>,
    position,
    style: {
      background: config.color,
      border: '2px solid #fff',
      borderRadius: '12px',
      padding: '10px',
      minWidth: '150px',
    },
  };
};

const getDefaultConfigForType = (type: WorkflowNode['type']): Record<string, unknown> => {
  switch (type) {
    case 'llm':
      return {
        model: 'gpt-4o',
        prompt: '',
        temperature: 0.7,
        max_tokens: 2000,
      };
    case 'code':
      return {
        language: 'python',
        code: '',
        timeout: 30,
        retry_count: 0,
      };
    case 'condition':
      return {
        expression: '',
        true_label: 'Yes',
        false_label: 'No',
      };
    case 'parallel':
      return {
        branch_count: 2,
        wait_for_all: true,
        aggregation: 'all',
      };
    case 'loop':
      return {
        max_iterations: 10,
        exit_condition: '',
        loop_variable: 'i',
        collect_results: true,
      };
    case 'http':
      return {
        url: '',
        method: 'GET',
        headers: '{}',
        body: '',
        timeout: 30,
        auth_type: 'none',
      };
    case 'human':
      return {
        message: '',
        timeout: 3600,
        required_role: 'user',
      };
    case 'sub_workflow':
      return {
        workflow_id: '',
        input_mapping: '{}',
        pass_context: true,
      };
    default:
      return {};
  }
};
