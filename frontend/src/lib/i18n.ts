import enUS from '@/locales/en-US.json';
import zhCN from '@/locales/zh-CN.json';
import jaJP from '@/locales/ja-JP.json';

// Supported locales
export const LOCALES = ['en-US', 'zh-CN', 'ja-JP'] as const;
export type Locale = (typeof LOCALES)[number];

// Default locale
export const DEFAULT_LOCALE: Locale = 'zh-CN';

// Storage key
export const LOCALE_STORAGE_KEY = 'app-locale';

// Translation resources
const resources: Record<Locale, Record<string, unknown>> = {
  'en-US': enUS,
  'zh-CN': zhCN,
  'ja-JP': jaJP,
};

/**
 * Resolve a nested key like "nav.dashboard" from a flat object.
 */
function getNestedValue(obj: Record<string, unknown>, key: string): string | undefined {
  const parts = key.split('.');
  let current: unknown = obj;
  for (const part of parts) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return undefined;
    }
    current = (current as Record<string, unknown>)[part];
  }
  return typeof current === 'string' ? current : undefined;
}

/**
 * Interpolate parameters into a template string.
 * Supports {name} style placeholders.
 * Also supports simple plural: {count, plural, one{...} other{...}}
 */
function interpolate(template: string, params?: Record<string, unknown>): string {
  if (!params) return template;

  // Handle plural form: {count, plural, one{singular} other{plural}}
  const pluralRegex = /\{(\w+),\s*plural,\s*one\{([^}]*)\}\s*other\{([^}]*)\}\}/g;
  let result = template.replace(pluralRegex, (_match, countKey, singular, plural) => {
    const count = Number(params[countKey]);
    if (isNaN(count)) return plural;
    return count === 1 ? singular : plural;
  });

  // Handle simple {key} interpolation
  result = result.replace(/\{(\w+)\}/g, (match, key) => {
    if (key in params) {
      const value = params[key];
      return value !== null && value !== undefined ? String(value) : match;
    }
    return match;
  });

  return result;
}

/**
 * Translate a key for the given locale.
 * Falls back to default locale, then returns the key itself.
 */
export function translate(locale: Locale, key: string, params?: Record<string, unknown>): string {
  const dict = resources[locale];
  if (dict) {
    const value = getNestedValue(dict, key);
    if (value !== undefined) {
      return interpolate(value, params);
    }
  }

  // Fallback to default locale
  if (locale !== DEFAULT_LOCALE) {
    const fallbackDict = resources[DEFAULT_LOCALE];
    if (fallbackDict) {
      const fallbackValue = getNestedValue(fallbackDict, key);
      if (fallbackValue !== undefined) {
        return interpolate(fallbackValue, params);
      }
    }
  }

  // Return key as last resort
  return key;
}

/**
 * Detect browser locale and match to a supported locale.
 */
export function detectBrowserLocale(): Locale {
  if (typeof navigator === 'undefined') return DEFAULT_LOCALE;

  const browserLang = navigator.language || (navigator as { userLanguage?: string }).userLanguage;
  if (!browserLang) return DEFAULT_LOCALE;

  // Exact match
  if ((LOCALES as readonly string[]).includes(browserLang)) {
    return browserLang as Locale;
  }

  // Prefix match (e.g., "zh" matches "zh-CN")
  const prefix = browserLang.split('-')[0];
  const match = LOCALES.find((l) => l.startsWith(prefix));
  return match ?? DEFAULT_LOCALE;
}

/**
 * Load saved locale from localStorage, falling back to browser detection.
 */
export function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE;

  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (saved && (LOCALES as readonly string[]).includes(saved)) {
      return saved as Locale;
    }
  } catch {
    // localStorage may be unavailable
  }

  return detectBrowserLocale();
}

/**
 * Persist locale choice to localStorage.
 */
export function saveLocale(locale: Locale): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Ignore write errors
  }
}

/**
 * Get the HTML lang attribute value for a locale.
 */
export function getHtmlLang(locale: Locale): string {
  return locale;
}
