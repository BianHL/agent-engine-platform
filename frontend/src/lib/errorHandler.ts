'use client';
import { message, notification } from 'antd';
import { AxiosError } from 'axios';

interface ErrorConfig {
  showMessage?: boolean;
  showNotification?: boolean;
  logToConsole?: boolean;
  reportToAnalytics?: boolean;
  fallbackMessage?: string;
}

const defaultConfig: ErrorConfig = {
  showMessage: true,
  showNotification: false,
  logToConsole: true,
  reportToAnalytics: true,
  fallbackMessage: 'An unexpected error occurred',
};

// Error types
export class AppError extends Error {
  code: string;
  statusCode?: number;
  details?: Record<string, unknown>;

  constructor(message: string, code: string, statusCode?: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export class NetworkError extends AppError {
  constructor(message: string = 'Network error. Please check your connection.') {
    super(message, 'NETWORK_ERROR', 0);
    this.name = 'NetworkError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication failed. Please log in again.') {
    super(message, 'AUTH_ERROR', 401);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'You do not have permission to perform this action.') {
    super(message, 'FORBIDDEN', 403);
    this.name = 'AuthorizationError';
  }
}

export class ValidationError extends AppError {
  fields?: Record<string, string[]>;

  constructor(message: string = 'Validation failed.', fields?: Record<string, string[]>) {
    super(message, 'VALIDATION_ERROR', 400);
    this.name = 'ValidationError';
    this.fields = fields;
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string = 'Resource') {
    super(`${resource} not found.`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends AppError {
  retryAfter?: number;

  constructor(retryAfter?: number) {
    super('Too many requests. Please try again later.', 'RATE_LIMIT', 429);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

export class TimeoutError extends AppError {
  constructor(message: string = 'Request timed out. Please try again.') {
    super(message, 'TIMEOUT', 0);
    this.name = 'TimeoutError';
  }
}

// Parse error from API response
export function parseApiError(error: AxiosError): AppError {
  const status = error.response?.status;
  const data = error.response?.data as any;

  const message = data?.detail || data?.message || error.message;
  const code = data?.code || 'UNKNOWN_ERROR';
  const details = data?.details;

  switch (status) {
    case 400:
      return new ValidationError(message, data?.fields);
    case 401:
      return new AuthenticationError(message);
    case 403:
      return new AuthorizationError(message);
    case 404:
      return new NotFoundError();
    case 429:
      const retryAfter = error.response?.headers?.['retry-after'];
      return new RateLimitError(retryAfter ? parseInt(retryAfter) : undefined);
    case 500:
    case 502:
    case 503:
    case 504:
      return new AppError(message, 'SERVER_ERROR', status, details);
    default:
      if (!error.response) {
        if (error.code === 'ECONNABORTED') {
          return new TimeoutError();
        }
        return new NetworkError();
      }
      return new AppError(message, code, status, details);
  }
}

// Handle error with user feedback
export function handleError(error: unknown, config: ErrorConfig = {}) {
  const mergedConfig = { ...defaultConfig, ...config };

  let appError: AppError;

  if (error instanceof AppError) {
    appError = error;
  } else if (error instanceof AxiosError) {
    appError = parseApiError(error);
  } else if (error instanceof Error) {
    appError = new AppError(error.message, 'UNKNOWN_ERROR');
  } else {
    appError = new AppError(String(error), 'UNKNOWN_ERROR');
  }

  // Log to console
  if (mergedConfig.logToConsole) {
    console.error(`[${appError.code}]`, appError.message, appError.details);
  }

  // Show message
  if (mergedConfig.showMessage) {
    const duration = appError instanceof RateLimitError ? 6 : 4;

    switch (appError.statusCode) {
      case 400:
        message.error(appError.message);
        break;
      case 401:
        message.warning(appError.message);
        break;
      case 403:
        message.error(appError.message);
        break;
      case 404:
        message.warning(appError.message);
        break;
      case 429:
        message.warning(appError.message);
        break;
      default:
        message.error(appError.message || mergedConfig.fallbackMessage);
    }
  }

  // Show notification for critical errors
  if (mergedConfig.showNotification && appError.statusCode && appError.statusCode >= 500) {
    notification.error({
      message: 'Server Error',
      description: appError.message,
      duration: 6,
    });
  }

  // Handle authentication errors
  if (appError instanceof AuthenticationError) {
    // Redirect to login
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }

  return appError;
}

// Async error wrapper
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  config?: ErrorConfig
): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    handleError(error, config);
    return null;
  }
}

// Error boundary fallback component props
export interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

// Global error handler for unhandled promise rejections
export function setupGlobalErrorHandlers() {
  if (typeof window === 'undefined') return;

  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    handleError(event.reason, { showMessage: true, showNotification: true });
  });

  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    handleError(event.error, { showMessage: false, showNotification: true });
  });
}

// Retry logic with exponential backoff
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    baseDelay?: number;
    maxDelay?: number;
    retryOn?: (error: unknown) => boolean;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    retryOn = () => true,
  } = options;

  let lastError: unknown;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt === maxRetries || !retryOn(error)) {
        throw error;
      }

      const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
      const jitter = delay * 0.1 * Math.random();
      await new Promise(resolve => setTimeout(resolve, delay + jitter));
    }
  }

  throw lastError;
}
