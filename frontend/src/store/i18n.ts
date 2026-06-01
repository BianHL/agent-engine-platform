import { create } from 'zustand';
import {
  type Locale,
  DEFAULT_LOCALE,
  getInitialLocale,
  saveLocale,
  translate,
} from '@/lib/i18n';

interface I18nState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, unknown>) => string;
}

const initialLocale = getInitialLocale();

export const useI18nStore = create<I18nState>((set, get) => ({
  locale: initialLocale,

  setLocale: (locale: Locale) => {
    saveLocale(locale);
    set({ locale });
  },

  t: (key: string, params?: Record<string, unknown>): string => {
    return translate(get().locale, key, params);
  },
}));
