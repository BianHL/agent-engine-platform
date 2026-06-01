'use client';
import { useCallback } from 'react';
import { useI18nStore } from '@/store/i18n';
import { type Locale, LOCALES } from '@/lib/i18n';

/**
 * Translation hook for React components.
 *
 * Usage:
 *   const { t, locale, setLocale, locales } = useTranslation();
 *   t('nav.dashboard')               // basic
 *   t('pagination.total', { total: 42 })  // with params
 *   t('items', { count: 1 })         // plural (requires "one{...} other{...}" in translation)
 */
export function useTranslation() {
  const locale = useI18nStore((s) => s.locale);
  const setLocale = useI18nStore((s) => s.setLocale);
  const storeT = useI18nStore((s) => s.t);

  const t = useCallback(
    (key: string, params?: Record<string, unknown>): string => {
      return storeT(key, params);
    },
    [storeT],
  );

  return {
    t,
    locale,
    setLocale,
    locales: LOCALES as readonly Locale[],
  };
}

export default useTranslation;
