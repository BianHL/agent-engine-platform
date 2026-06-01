'use client';

interface AnalyticsEvent {
  category: string;
  action: string;
  label?: string;
  value?: number;
  properties?: Record<string, unknown>;
}

interface AnalyticsConfig {
  enabled: boolean;
  debug: boolean;
  endpoint?: string;
}

class Analytics {
  private config: AnalyticsConfig;
  private queue: AnalyticsEvent[] = [];
  private flushInterval: NodeJS.Timeout | null = null;

  constructor(config: AnalyticsConfig) {
    this.config = config;

    if (config.enabled) {
      this.startFlushInterval();
    }
  }

  private startFlushInterval() {
    this.flushInterval = setInterval(() => {
      this.flush();
    }, 30000); // Flush every 30 seconds
  }

  private stopFlushInterval() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
  }

  // Track an event
  track(event: AnalyticsEvent) {
    if (!this.config.enabled) return;

    const enrichedEvent: AnalyticsEvent = {
      ...event,
      properties: {
        ...event.properties,
        timestamp: Date.now(),
        url: typeof window !== 'undefined' ? window.location.href : undefined,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      },
    };

    this.queue.push(enrichedEvent);

    if (this.config.debug) {
      console.log('[Analytics]', enrichedEvent);
    }

    // Flush if queue is large
    if (this.queue.length >= 50) {
      this.flush();
    }
  }

  // Track page view
  pageView(page: string, title?: string) {
    this.track({
      category: 'Navigation',
      action: 'Page View',
      label: page,
      properties: { title },
    });
  }

  // Track user action
  action(category: string, action: string, label?: string, value?: number) {
    this.track({ category, action, label, value });
  }

  // Track agent interaction
  agentAction(action: string, agentId: string, properties?: Record<string, unknown>) {
    this.track({
      category: 'Agent',
      action,
      label: agentId,
      properties,
    });
  }

  // Track workflow execution
  workflowAction(action: string, workflowId: string, properties?: Record<string, unknown>) {
    this.track({
      category: 'Workflow',
      action,
      label: workflowId,
      properties,
    });
  }

  // Track knowledge base operation
  knowledgeAction(action: string, kbId: string, properties?: Record<string, unknown>) {
    this.track({
      category: 'Knowledge',
      action,
      label: kbId,
      properties,
    });
  }

  // Track tool usage
  toolAction(action: string, toolName: string, properties?: Record<string, unknown>) {
    this.track({
      category: 'Tool',
      action,
      label: toolName,
      properties,
    });
  }

  // Track error
  error(errorType: string, errorMessage: string, properties?: Record<string, unknown>) {
    this.track({
      category: 'Error',
      action: errorType,
      label: errorMessage,
      properties,
    });
  }

  // Track performance
  performance(metric: string, value: number, properties?: Record<string, unknown>) {
    this.track({
      category: 'Performance',
      action: metric,
      value,
      properties,
    });
  }

  // Track user engagement
  engagement(action: string, properties?: Record<string, unknown>) {
    this.track({
      category: 'Engagement',
      action,
      properties,
    });
  }

  // Flush events to server
  async flush() {
    if (this.queue.length === 0) return;

    const events = [...this.queue];
    this.queue = [];

    if (!this.config.endpoint) {
      if (this.config.debug) {
        console.log('[Analytics] Flushing events (no endpoint):', events);
      }
      return;
    }

    try {
      await fetch(this.config.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events }),
      });
    } catch (error) {
      if (this.config.debug) {
        console.error('[Analytics] Failed to flush events:', error);
      }
      // Re-queue failed events
      this.queue = [...events, ...this.queue];
    }
  }

  // Set user identity
  identify(userId: string, properties?: Record<string, unknown>) {
    if (!this.config.enabled) return;

    this.track({
      category: 'User',
      action: 'Identify',
      label: userId,
      properties,
    });
  }

  // Reset analytics state
  reset() {
    this.queue = [];
  }

  // Update configuration
  updateConfig(config: Partial<AnalyticsConfig>) {
    this.config = { ...this.config, ...config };

    if (config.enabled && !this.flushInterval) {
      this.startFlushInterval();
    } else if (!config.enabled && this.flushInterval) {
      this.stopFlushInterval();
    }
  }
}

// Create singleton instance
export const analytics = new Analytics({
  enabled: process.env.NODE_ENV === 'production',
  debug: process.env.NODE_ENV === 'development',
  endpoint: '/api/v1/analytics',
});

// React hook for analytics
export function useAnalytics() {
  return {
    track: analytics.track.bind(analytics),
    pageView: analytics.pageView.bind(analytics),
    action: analytics.action.bind(analytics),
    agentAction: analytics.agentAction.bind(analytics),
    workflowAction: analytics.workflowAction.bind(analytics),
    knowledgeAction: analytics.knowledgeAction.bind(analytics),
    toolAction: analytics.toolAction.bind(analytics),
    error: analytics.error.bind(analytics),
    performance: analytics.performance.bind(analytics),
    engagement: analytics.engagement.bind(analytics),
    identify: analytics.identify.bind(analytics),
  };
}

// Performance monitoring
export function measurePerformance(name: string, fn: () => Promise<void>) {
  return async () => {
    const start = performance.now();
    try {
      await fn();
    } finally {
      const duration = performance.now() - start;
      analytics.performance(name, duration);
    }
  };
}

// Page load performance
export function trackPageLoad() {
  if (typeof window === 'undefined') return;

  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navigation) {
      analytics.performance('Page Load', navigation.loadEventEnd - navigation.startTime);
      analytics.performance('DOM Content Loaded', navigation.domContentLoadedEventEnd - navigation.startTime);
      analytics.performance('First Paint', navigation.responseEnd - navigation.startTime);
    }
  });
}
