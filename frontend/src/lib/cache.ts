'use client';
import { useState, useCallback, useEffect } from 'react';

interface CacheConfig {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum number of items
  storage?: 'memory' | 'localStorage' | 'sessionStorage';
}

interface CacheItem<T> {
  value: T;
  timestamp: number;
  ttl: number;
}

class Cache<T = unknown> {
  private memoryCache: Map<string, CacheItem<T>> = new Map();
  private config: Required<CacheConfig>;

  constructor(config: CacheConfig = {}) {
    this.config = {
      ttl: config.ttl ?? 5 * 60 * 1000, // 5 minutes default
      maxSize: config.maxSize ?? 100,
      storage: config.storage ?? 'memory',
    };
  }

  // Get item from cache
  get(key: string): T | null {
    const item = this.getInternal(key);
    if (!item) return null;

    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      this.delete(key);
      return null;
    }

    return item.value;
  }

  // Set item in cache
  set(key: string, value: T, ttl?: number): void {
    // Enforce max size
    if (this.memoryCache.size >= this.config.maxSize) {
      const firstKey = this.memoryCache.keys().next().value;
      if (firstKey) this.delete(firstKey);
    }

    const item: CacheItem<T> = {
      value,
      timestamp: Date.now(),
      ttl: ttl ?? this.config.ttl,
    };

    this.setInternal(key, item);
  }

  // Delete item from cache
  delete(key: string): boolean {
    this.deleteInternal(key);
    return true;
  }

  // Check if key exists and is not expired
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  // Clear all items
  clear(): void {
    if (this.config.storage === 'memory') {
      this.memoryCache.clear();
    } else {
      this.clearStorage();
    }
  }

  // Get cache size
  get size(): number {
    if (this.config.storage === 'memory') {
      return this.memoryCache.size;
    }
    return this.getStorageKeys().length;
  }

  // Get all keys
  keys(): string[] {
    if (this.config.storage === 'memory') {
      return Array.from(this.memoryCache.keys());
    }
    return this.getStorageKeys();
  }

  // Get or set with factory function
  async getOrSet(key: string, factory: () => Promise<T>, ttl?: number): Promise<T> {
    const cached = this.get(key);
    if (cached !== null) return cached;

    const value = await factory();
    this.set(key, value, ttl);
    return value;
  }

  // Internal methods based on storage type
  private getInternal(key: string): CacheItem<T> | null {
    if (this.config.storage === 'memory') {
      return this.memoryCache.get(key) ?? null;
    }

    try {
      const storage = this.getStorage();
      const item = storage.getItem(this.getStorageKey(key));
      if (!item) return null;
      return JSON.parse(item);
    } catch {
      return null;
    }
  }

  private setInternal(key: string, item: CacheItem<T>): void {
    if (this.config.storage === 'memory') {
      this.memoryCache.set(key, item);
      return;
    }

    try {
      const storage = this.getStorage();
      storage.setItem(this.getStorageKey(key), JSON.stringify(item));
    } catch {
      // Storage might be full
      this.evictOldest();
    }
  }

  private deleteInternal(key: string): void {
    if (this.config.storage === 'memory') {
      this.memoryCache.delete(key);
      return;
    }

    try {
      const storage = this.getStorage();
      storage.removeItem(this.getStorageKey(key));
    } catch {
      // Ignore errors
    }
  }

  private clearStorage(): void {
    try {
      const storage = this.getStorage();
      const keys = this.getStorageKeys();
      keys.forEach(key => storage.removeItem(this.getStorageKey(key)));
    } catch {
      // Ignore errors
    }
  }

  private getStorage(): Storage {
    if (this.config.storage === 'localStorage') {
      return localStorage;
    }
    return sessionStorage;
  }

  private getStorageKey(key: string): string {
    return `cache:${key}`;
  }

  private getStorageKeys(): string[] {
    try {
      const storage = this.getStorage();
      const keys: string[] = [];
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key?.startsWith('cache:')) {
          keys.push(key.replace('cache:', ''));
        }
      }
      return keys;
    } catch {
      return [];
    }
  }

  private evictOldest(): void {
    try {
      const storage = this.getStorage();
      const keys = this.getStorageKeys();
      let oldestKey: string | null = null;
      let oldestTime = Infinity;

      keys.forEach(key => {
        const item = this.getInternal(key);
        if (item && item.timestamp < oldestTime) {
          oldestTime = item.timestamp;
          oldestKey = key;
        }
      });

      if (oldestKey) {
        storage.removeItem(this.getStorageKey(oldestKey));
      }
    } catch {
      // Ignore errors
    }
  }
}

// Create cache instances
export const memoryCache = new Cache({ storage: 'memory', ttl: 5 * 60 * 1000 });
export const localStorageCache = new Cache({ storage: 'localStorage', ttl: 24 * 60 * 60 * 1000 });
export const sessionStorageCache = new Cache({ storage: 'sessionStorage', ttl: 30 * 60 * 1000 });

// Cache keys
export const CACHE_KEYS = {
  USER: 'user',
  AGENTS: 'agents',
  KNOWLEDGE_BASES: 'knowledge_bases',
  WORKFLOWS: 'workflows',
  TOOLS: 'tools',
  MODELS: 'models',
  SETTINGS: 'settings',
  THEME: 'theme',
  LANGUAGE: 'language',
} as const;

// Cache utilities
export function cacheKey(...parts: (string | number | undefined)[]): string {
  return parts.filter(Boolean).join(':');
}

// React hook for cache
export function useCache<T>(key: string, fetcher: () => Promise<T>, ttl?: number) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Check cache first
        const cached = memoryCache.get(key) as T | null;
        if (cached !== null) {
          setData(cached);
          setLoading(false);
          return;
        }

        // Fetch fresh data
        setLoading(true);
        const result = await fetcher();
        memoryCache.set(key, result, ttl);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [key, ttl, fetcher]);

  const invalidate = useCallback(() => {
    memoryCache.delete(key);
  }, [key]);

  return { data, loading, error, invalidate };
}

// Prefetch data into cache
export async function prefetch<T>(key: string, fetcher: () => Promise<T>, ttl?: number): Promise<void> {
  if (memoryCache.has(key)) return;

  try {
    const data = await fetcher();
    memoryCache.set(key, data, ttl);
  } catch (error) {
    console.error(`Prefetch failed for key: ${key}`, error);
  }
}

// Invalidate cache entries matching a pattern
export function invalidatePattern(pattern: string | RegExp): void {
  const keys = memoryCache.keys();
  const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;

  keys.forEach(key => {
    if (regex.test(key)) {
      memoryCache.delete(key);
    }
  });
}

// Cache middleware for API calls
export function withCache<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  keyFn: (...args: Parameters<T>) => string,
  ttl?: number
): T {
  return (async (...args: Parameters<T>) => {
    const key = keyFn(...args);
    return memoryCache.getOrSet(key, () => fn(...args), ttl);
  }) as T;
}
