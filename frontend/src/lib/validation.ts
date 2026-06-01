'use client';
import { useState } from 'react';
import { z } from 'zod';

// Common validation schemas
export const commonSchemas = {
  // String validations
  nonEmptyString: z.string().min(1, 'This field is required'),
  optionalString: z.string().optional(),

  // Email
  email: z.string().email('Invalid email address'),

  // URL
  url: z.string().url('Invalid URL'),

  // Password
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),

  // Username
  username: z.string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, hyphens, and underscores'),

  // Number validations
  positiveNumber: z.number().positive('Must be a positive number'),
  nonNegativeNumber: z.number().min(0, 'Must be a non-negative number'),
  integer: z.number().int('Must be an integer'),
  percentage: z.number().min(0).max(100, 'Must be between 0 and 100'),

  // UUID
  uuid: z.string().uuid('Invalid UUID format'),

  // JSON
  json: z.string().refine(
    (val) => {
      try {
        JSON.parse(val);
        return true;
      } catch {
        return false;
      }
    },
    { message: 'Invalid JSON format' }
  ),

  // Date
  dateString: z.string().datetime('Invalid date format'),

  // Array of strings
  stringArray: z.array(z.string()),

  // Object
  record: z.record(z.string(), z.unknown()),
};

// Agent validation schemas
export const agentSchemas = {
  create: z.object({
    name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
    description: z.string().max(500, 'Description must be less than 500 characters').optional(),
    model_provider: z.string().optional(),
    model_name: z.string().optional(),
    system_prompt: z.string().max(10000, 'System prompt must be less than 10000 characters').optional(),
    tools: z.array(z.string()).optional(),
    knowledge_base_ids: z.array(z.string()).optional(),
  }),

  update: z.object({
    name: z.string().min(1).max(100).optional(),
    description: z.string().max(500).optional(),
    system_prompt: z.string().max(10000).optional(),
    tools: z.array(z.string()).optional(),
    knowledge_base_ids: z.array(z.string()).optional(),
  }),
};

// Knowledge base validation schemas
export const knowledgeSchemas = {
  create: z.object({
    name: z.string().min(1, 'Name is required').max(100),
    description: z.string().max(500).optional(),
    embedding_model: z.string().min(1, 'Embedding model is required'),
    chunk_size: z.number().int().min(100).max(4000).optional().default(500),
    chunk_overlap: z.number().int().min(0).max(500).optional().default(50),
  }),
};

// Workflow validation schemas
export const workflowSchemas = {
  create: z.object({
    name: z.string().min(1, 'Name is required').max(100),
    description: z.string().max(500).optional(),
    nodes: z.array(z.object({
      id: z.string(),
      type: z.string(),
      label: z.string(),
      config: z.record(z.string(), z.unknown()).optional(),
      position: z.object({ x: z.number(), y: z.number() }),
    })).optional(),
    edges: z.array(z.object({
      id: z.string(),
      source: z.string(),
      target: z.string(),
      sourceHandle: z.string().optional(),
      targetHandle: z.string().optional(),
      label: z.string().optional(),
      animated: z.boolean().optional(),
    })).optional(),
  }),
};

// Model validation schemas
export const modelSchemas = {
  createProvider: z.object({
    name: z.string().min(1, 'Name is required').max(100),
    provider_type: z.enum(['openai', 'anthropic', 'azure_openai', 'deepseek', 'ollama', 'custom']),
    api_key: z.string().min(1, 'API key is required'),
    api_base: z.string().url().optional(),
  }),

  createConfig: z.object({
    provider_id: z.string().uuid(),
    model_name: z.string().min(1, 'Model name is required'),
    model_type: z.enum(['llm', 'embedding', 'reranker']),
    display_name: z.string().min(1, 'Display name is required'),
    is_default: z.boolean().optional(),
  }),
};

// Tool validation schemas
export const toolSchemas = {
  create: z.object({
    name: z.string().min(1, 'Name is required').max(100),
    description: z.string().max(500).optional(),
    tool_type: z.enum(['custom', 'mcp']),
    api_schema: z.string().optional().refine(
      (val) => {
        if (!val) return true;
        try {
          JSON.parse(val);
          return true;
        } catch {
          return false;
        }
      },
      { message: 'Invalid JSON in API schema' }
    ),
  }),
};

// User validation schemas
export const userSchemas = {
  login: z.object({
    username: z.string().min(1, 'Username is required'),
    password: z.string().min(1, 'Password is required'),
  }),

  register: z.object({
    username: commonSchemas.username,
    email: commonSchemas.email,
    password: commonSchemas.password,
    confirmPassword: z.string(),
  }).refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  }),

  updateProfile: z.object({
    email: commonSchemas.email.optional(),
    currentPassword: z.string().optional(),
    newPassword: commonSchemas.password.optional(),
  }),
};

// Validation helper functions
export function validateField<T>(schema: z.ZodType<T>, value: unknown): {
  success: boolean;
  error?: string;
  data?: T;
} {
  const result = schema.safeParse(value);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return {
    success: false,
    error: result.error.issues[0]?.message ?? 'Validation failed',
  };
}

export function validateForm<T>(schema: z.ZodType<T>, data: unknown): {
  success: boolean;
  errors?: Record<string, string>;
  data?: T;
} {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }

  const errors: Record<string, string> = {};
  result.error.issues.forEach((error: z.ZodIssue) => {
    const path = error.path.join('.');
    errors[path] = error.message;
  });

  return { success: false, errors };
}

// Custom validation rules
export const customRules = {
  // Validate JSON string
  isValidJson: (value: string): boolean => {
    try {
      JSON.parse(value);
      return true;
    } catch {
      return false;
    }
  },

  // Validate URL format
  isValidUrl: (value: string): boolean => {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  },

  // Validate email format
  isValidEmail: (value: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  },

  // Validate password strength
  isStrongPassword: (value: string): boolean => {
    return (
      value.length >= 8 &&
      /[A-Z]/.test(value) &&
      /[a-z]/.test(value) &&
      /[0-9]/.test(value)
    );
  },

  // Validate UUID format
  isValidUuid: (value: string): boolean => {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
  },

  // Validate date string
  isValidDate: (value: string): boolean => {
    return !isNaN(Date.parse(value));
  },

  // Validate number range
  isInRange: (value: number, min: number, max: number): boolean => {
    return value >= min && value <= max;
  },

  // Validate string length
  hasLength: (value: string, min: number, max?: number): boolean => {
    if (value.length < min) return false;
    if (max && value.length > max) return false;
    return true;
  },
};

// Form validation hook
export function useFormValidation<T>(schema: z.ZodType<T>) {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (data: unknown): boolean => {
    const result = validateForm(schema, data);
    if (!result.success) {
      setErrors(result.errors ?? {});
      return false;
    }
    setErrors({});
    return true;
  };

  const clearErrors = () => setErrors({});

  const getFieldError = (field: string): string | undefined => errors[field];

  const hasErrors = Object.keys(errors).length > 0;

  return { errors, validate, clearErrors, getFieldError, hasErrors };
}


