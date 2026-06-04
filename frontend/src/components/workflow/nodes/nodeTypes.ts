import type { WorkflowNode } from '@/types';

export const NODE_TYPES = [
  // ── Flow control ──────────────────────────────────────────
  {
    type: 'start' as const,
    label: 'Start',
    color: '#52c41a',
    icon: '▶️',
    description: 'Workflow entry point — define input variables',
    category: 'flow',
  },
  {
    type: 'end' as const,
    label: 'End',
    color: '#ff4d4f',
    icon: '⏹️',
    description: 'Workflow exit point — define output format',
    category: 'flow',
  },
  {
    type: 'condition' as const,
    label: 'Condition',
    color: '#faad14',
    icon: '🔀',
    description: 'IF/ELSE conditional branching',
    category: 'flow',
  },
  {
    type: 'parallel' as const,
    label: 'Parallel',
    color: '#52c41a',
    icon: '⚙️',
    description: 'Execute branches in parallel',
    category: 'flow',
  },
  {
    type: 'iteration' as const,
    label: 'Iteration',
    color: '#722ed1',
    icon: '🔄',
    description: 'Loop over arrays with sub-workflow',
    category: 'flow',
  },
  // ── LLM / AI ─────────────────────────────────────────────
  {
    type: 'llm' as const,
    label: 'LLM',
    color: '#1890ff',
    icon: '🤖',
    description: 'Large Language Model inference',
    category: 'ai',
  },
  {
    type: 'knowledge' as const,
    label: 'Knowledge',
    color: '#9254de',
    icon: '📚',
    description: 'Retrieve from knowledge base (RAG)',
    category: 'ai',
  },
  {
    type: 'question_classifier' as const,
    label: 'Classifier',
    color: '#eb2f96',
    icon: '🏷️',
    description: 'Classify user input into categories',
    category: 'ai',
  },
  {
    type: 'parameter_extractor' as const,
    label: 'Extractor',
    color: '#fa8c16',
    icon: '🔍',
    description: 'Extract structured data from text',
    category: 'ai',
  },
  // ── Data / Transform ─────────────────────────────────────
  {
    type: 'code' as const,
    label: 'Code',
    color: '#eb2f96',
    icon: '⚡',
    description: 'Execute Python/JavaScript code',
    category: 'data',
  },
  {
    type: 'template' as const,
    label: 'Template',
    color: '#13c2c2',
    icon: '📝',
    description: 'Render Jinja2/text templates',
    category: 'data',
  },
  {
    type: 'variable' as const,
    label: 'Variable',
    color: '#2f54eb',
    icon: '📦',
    description: 'Assign and transform variables',
    category: 'data',
  },
  // ── Integration ──────────────────────────────────────────
  {
    type: 'http' as const,
    label: 'HTTP',
    color: '#13c2c2',
    icon: '🌐',
    description: 'Make HTTP requests',
    category: 'integration',
  },
  {
    type: 'tool' as const,
    label: 'Tool',
    color: '#fa541c',
    icon: '🔧',
    description: 'Call external tools',
    category: 'integration',
  },
  {
    type: 'human' as const,
    label: 'Human',
    color: '#fa541c',
    icon: '👤',
    description: 'Human review/approval',
    category: 'integration',
  },
  {
    type: 'sub_workflow' as const,
    label: 'Sub Workflow',
    color: '#2f54eb',
    icon: '📋',
    description: 'Execute nested workflow',
    category: 'integration',
  },
  // ── Chatflow ─────────────────────────────────────────────
  {
    type: 'answer' as const,
    label: 'Answer',
    color: '#52c41a',
    icon: '💬',
    description: 'Chatflow response node',
    category: 'chatflow',
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
    case 'start':
      return {
        input_variables: [],
        description: 'Workflow entry point',
      };
    case 'end':
      return {
        output_variables: [],
        description: 'Workflow exit point',
      };
    case 'llm':
      return {
        model: 'gpt-4o',
        system_prompt: '',
        user_prompt: '',
        temperature: 0.7,
        max_tokens: 2000,
        context_variable: '',
        memory_enabled: false,
      };
    case 'knowledge':
      return {
        knowledge_base_ids: [],
        query_variable: '{{input}}',
        top_k: 5,
        score_threshold: 0.5,
        retrieval_mode: 'hybrid',
      };
    case 'question_classifier':
      return {
        input_variable: '{{input}}',
        classes: [
          { name: 'Class 1', description: 'Description' },
        ],
        model: 'gpt-4o-mini',
      };
    case 'parameter_extractor':
      return {
        input_variable: '{{input}}',
        model: 'gpt-4o-mini',
        parameters: [
          { name: 'param1', type: 'string', description: 'Description', required: true },
        ],
      };
    case 'code':
      return {
        language: 'python',
        code: '# Input: variables from previous nodes\n# Output: return a dict\n\nresult = {}\n',
        timeout: 30,
        input_variables: {},
        output_variables: ['result'],
      };
    case 'template':
      return {
        template: 'Hello {{name}}, welcome!',
        input_variables: {},
      };
    case 'variable':
      return {
        operations: [
          { variable: 'output', operator: 'assign', value: '{{input}}' },
        ],
      };
    case 'condition':
      return {
        conditions: [
          { variable: '', operator: '==', value: '', label: 'IF' },
        ],
        else_label: 'ELSE',
      };
    case 'parallel':
      return {
        branch_count: 2,
        wait_for_all: true,
      };
    case 'iteration':
      return {
        input_variable: '{{items}}',
        max_iterations: 100,
        output_mode: 'collect',
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
    case 'tool':
      return {
        tool_name: '',
        tool_params: {},
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
    case 'answer':
      return {
        answer_template: '{{output}}',
        variables: {},
      };
    default:
      return {};
  }
};
