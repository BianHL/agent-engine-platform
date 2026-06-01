'use client';
import { ThemeConfig } from 'antd';

// ─────────────────────────────────────────────────────────────
// Design Tokens — synced with DESIGN.md (v2.0)
// Soft Editorial Warmth: Warm Parchment + Olive Green + Warm Gold
// ─────────────────────────────────────────────────────────────

export const tokens = {
  colors: {
    // Backgrounds
    bg: '#f5efe6',
    bgSecondary: '#ece3d6',
    bgDark: '#1c1917',
    bgDarkSecondary: '#252220',

    // Panels (glassmorphism)
    panel: 'rgba(255, 255, 255, 0.74)',
    panelStrong: 'rgba(255, 255, 255, 0.92)',
    panelDark: 'rgba(40, 36, 33, 0.74)',
    panelDarkStrong: 'rgba(40, 36, 33, 0.92)',

    // Text
    text: '#26221e',
    textDark: '#e8e2da',
    muted: 'rgba(38, 34, 30, 0.58)',
    mutedDark: 'rgba(232, 226, 218, 0.58)',

    // Accents
    accentOlive: '#7a8a6a',
    accentGold: '#c29a63',
    accentSage: '#9aaa88',

    // Semantic
    success: '#6f9b7c',
    warning: '#d0a45d',
    danger: '#c47a6e',
    dangerSecondary: '#cf7c73',

    // Borders
    line: 'rgba(86, 68, 54, 0.10)',
    lineStrong: 'rgba(86, 68, 54, 0.18)',
    lineDark: 'rgba(160, 150, 138, 0.10)',
    lineDarkStrong: 'rgba(160, 150, 138, 0.18)',

    // Shadows (warm-tinted)
    shadow: '0 18px 50px rgba(74, 60, 48, 0.10)',
    shadowSoft: '0 12px 28px rgba(74, 60, 48, 0.06)',
    shadowButton: '0 14px 28px rgba(168, 149, 106, 0.18)',
    focusRing: '0 0 0 3px rgba(122, 138, 106, 0.12)',

    // Overlay
    overlay: 'rgba(0, 0, 0, 0.35)',
    overlayDark: 'rgba(0, 0, 0, 0.65)',
  },

  typography: {
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontFamilySerif:
      "ui-serif, Georgia, Cambria, 'Times New Roman', serif",
    fontFamilyMono:
      "'SF Mono', 'Fira Code', 'JetBrains Mono', ui-monospace, monospace",
    fontSize: 14,
    fontSizeSM: 12,
    fontSizeLG: 16,
    lineHeight: 1.6,
  },

  radius: {
    sm: 12,
    md: 16,
    lg: 22,
    xl: 30,
    full: 999,
  },

  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    '2xl': 24,
    '3xl': 28,
  },

  motion: {
    easeDefault: 'ease',
    easeSmooth: 'cubic-bezier(.2,1,.2,1)',
    easeDrift: 'ease-in-out',
    durationFast: '180ms',
    durationNormal: '200ms',
    durationSlow: '300ms',
    durationFloatIn: '650ms',
    durationDrift: '12s',
    durationPulse: '1.5s',
  },

  breakpoints: {
    xs: 480,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
    xxl: 1600,
  },
} as const;

// ─────────────────────────────────────────────────────────────
// Ant Design Theme Config (mapped to new tokens)
// ─────────────────────────────────────────────────────────────

export const defaultTheme: ThemeConfig = {
  token: {
    // Brand — mapped to olive green
    colorPrimary: tokens.colors.accentOlive,
    colorSuccess: tokens.colors.success,
    colorWarning: tokens.colors.warning,
    colorError: tokens.colors.danger,
    colorInfo: tokens.colors.accentOlive,

    // Typography
    fontFamily: tokens.typography.fontFamily,
    fontSize: tokens.typography.fontSize,
    fontSizeSM: tokens.typography.fontSizeSM,
    fontSizeLG: tokens.typography.fontSizeLG,
    lineHeight: tokens.typography.lineHeight,

    // Radius
    borderRadius: tokens.radius.md,
    borderRadiusSM: tokens.radius.sm,
    borderRadiusLG: tokens.radius.lg,
    borderRadiusXS: 8,

    // Surfaces
    colorBgBase: tokens.colors.bg,
    colorBgContainer: tokens.colors.panelStrong,
    colorBgElevated: tokens.colors.panel,
    colorBgLayout: tokens.colors.bg,
    colorBgSpotlight: tokens.colors.text,

    // Text
    colorText: tokens.colors.text,
    colorTextSecondary: tokens.colors.muted,
    colorTextTertiary: 'rgba(38, 34, 30, 0.45)',
    colorTextQuaternary: 'rgba(38, 34, 30, 0.30)',
    colorTextHeading: tokens.colors.text,
    colorTextLabel: tokens.colors.muted,
    colorTextDescription: tokens.colors.muted,
    colorTextDisabled: 'rgba(38, 34, 30, 0.30)',
    colorTextLightSolid: '#ffffff',

    // Borders
    colorBorder: tokens.colors.line,
    colorBorderSecondary: tokens.colors.line,

    // Controls
    controlHeight: 40,
    controlHeightSM: 32,
    controlHeightLG: 48,
    controlOutline: tokens.colors.accentGold,
    controlItemBgHover: 'rgba(255, 255, 255, 0.50)',
    controlItemBgActive: 'rgba(255, 255, 255, 0.60)',

    // Shadows
    boxShadow: tokens.colors.shadowSoft,
    boxShadowSecondary: tokens.colors.shadow,
    boxShadowTertiary: '0 4px 12px rgba(74, 60, 48, 0.04)',

    // Misc
    colorLink: tokens.colors.accentOlive,
    colorLinkHover: tokens.colors.accentGold,
    colorLinkActive: tokens.colors.accentGold,
    colorSplit: tokens.colors.line,
    colorFill: 'rgba(255, 255, 255, 0.30)',
    colorFillSecondary: 'rgba(255, 255, 255, 0.40)',
    colorFillTertiary: 'rgba(255, 255, 255, 0.50)',
    colorFillQuaternary: 'rgba(255, 255, 255, 0.60)',
  },
  components: {
    Button: {
      controlHeight: 40,
      borderRadius: tokens.radius.md,
      primaryShadow: 'none',
      defaultShadow: 'none',
      dangerShadow: 'none',
      colorPrimary: tokens.colors.accentGold,
      colorPrimaryHover: '#b8956a',
      colorPrimaryActive: '#a08060',
    },
    Card: {
      borderRadiusLG: tokens.radius.lg,
      paddingLG: tokens.spacing['2xl'],
      colorBgContainer: tokens.colors.panelStrong,
      colorBorderSecondary: tokens.colors.line,
    },
    Input: {
      controlHeight: 40,
      borderRadius: tokens.radius.md,
      colorBgContainer: tokens.colors.panel,
      colorBorder: tokens.colors.line,
      activeBorderColor: tokens.colors.accentOlive,
      hoverBorderColor: tokens.colors.lineStrong,
      activeShadow: tokens.colors.focusRing,
    },
    Select: {
      controlHeight: 40,
      borderRadius: tokens.radius.md,
      colorBgContainer: tokens.colors.panel,
      colorBorder: tokens.colors.line,
    },
    Table: {
      borderRadius: tokens.radius.lg,
      headerBg: tokens.colors.panelStrong,
      headerColor: tokens.colors.muted,
      rowHoverBg: 'rgba(122, 138, 106, 0.04)',
      colorBgContainer: tokens.colors.panelStrong,
      borderColor: tokens.colors.line,
    },
    Modal: {
      borderRadiusLG: tokens.radius.xl,
      colorBgElevated: tokens.colors.panelStrong,
    },
    Drawer: {
      borderRadiusLG: tokens.radius.xl,
      colorBgElevated: tokens.colors.panelStrong,
    },
    Menu: {
      itemBorderRadius: tokens.radius.md,
      subMenuItemBorderRadius: tokens.radius.md,
      colorBgContainer: 'transparent',
      colorItemBgSelected: 'rgba(255, 255, 255, 0.60)',
      colorItemText: tokens.colors.muted,
      colorItemTextSelected: tokens.colors.text,
      colorItemTextHover: tokens.colors.text,
      colorItemBgHover: 'rgba(255, 255, 255, 0.50)',
    },
    Layout: {
      headerBg: tokens.colors.panel,
      headerColor: tokens.colors.text,
      headerHeight: 64,
      siderBg: tokens.colors.bgSecondary,
      bodyBg: tokens.colors.bg,
      footerBg: tokens.colors.panel,
      colorBgTrigger: tokens.colors.line,
    },
    Tabs: {
      borderRadius: tokens.radius.md,
      colorBorderSecondary: tokens.colors.line,
    },
    Tag: {
      borderRadiusSM: tokens.radius.full,
      defaultBg: 'rgba(255, 255, 255, 0.72)',
      defaultColor: tokens.colors.muted,
    },
    Badge: {
      colorBgContainer: tokens.colors.panelStrong,
    },
    Tooltip: {
      borderRadius: tokens.radius.md,
      colorTextLightSolid: tokens.colors.bg,
      colorBgSpotlight: tokens.colors.text,
    },
    Popover: {
      borderRadiusLG: tokens.radius.lg,
      colorBgElevated: tokens.colors.panelStrong,
    },
    Dropdown: {
      borderRadius: tokens.radius.md,
      colorBgElevated: tokens.colors.panelStrong,
    },
    Segmented: {
      borderRadius: tokens.radius.md,
      colorBgLayout: tokens.colors.panel,
    },
    Switch: {
      colorPrimary: tokens.colors.accentOlive,
      colorPrimaryHover: tokens.colors.accentSage,
    },
    Slider: {
      colorPrimary: tokens.colors.accentOlive,
      colorPrimaryBorderHover: tokens.colors.accentSage,
      trackBg: tokens.colors.accentOlive,
      trackHoverBg: tokens.colors.accentSage,
    },
    DatePicker: {
      borderRadius: tokens.radius.md,
      colorBgContainer: tokens.colors.panel,
      colorBorder: tokens.colors.line,
      activeBorderColor: tokens.colors.accentOlive,
      cellActiveWithRangeBg: 'rgba(122, 138, 106, 0.08)',
      cellHoverWithRangeBg: 'rgba(122, 138, 106, 0.04)',
    },
    Notification: {
      borderRadius: tokens.radius.lg,
      colorBgElevated: tokens.colors.panelStrong,
    },
    Message: {
      borderRadius: tokens.radius.md,
      colorBgElevated: tokens.colors.panel,
    },
    Skeleton: {
      color: tokens.colors.line,
      colorGradientEnd: 'rgba(86, 68, 54, 0.15)',
    },
    Empty: {
      colorTextDescription: tokens.colors.muted,
    },
  },
};

// ─────────────────────────────────────────────────────────────
// Dark Theme
// ─────────────────────────────────────────────────────────────

export const darkTheme: ThemeConfig = {
  ...defaultTheme,
  token: {
    ...defaultTheme.token,
    colorBgBase: tokens.colors.bgDark,
    colorBgContainer: tokens.colors.panelDarkStrong,
    colorBgElevated: tokens.colors.panelDark,
    colorBgLayout: tokens.colors.bgDark,
    colorBgSpotlight: tokens.colors.bg,

    colorText: tokens.colors.textDark,
    colorTextSecondary: tokens.colors.mutedDark,
    colorTextTertiary: 'rgba(232, 226, 218, 0.45)',
    colorTextQuaternary: 'rgba(232, 226, 218, 0.30)',
    colorTextHeading: tokens.colors.textDark,
    colorTextLabel: tokens.colors.mutedDark,
    colorTextDescription: tokens.colors.mutedDark,
    colorTextDisabled: 'rgba(232, 226, 218, 0.30)',
    colorTextLightSolid: tokens.colors.bgDark,

    colorBorder: tokens.colors.lineDark,
    colorBorderSecondary: tokens.colors.lineDark,

    controlOutline: tokens.colors.accentGold,
    controlItemBgHover: 'rgba(40, 36, 33, 0.50)',
    controlItemBgActive: 'rgba(40, 36, 33, 0.60)',

    colorFill: 'rgba(40, 36, 33, 0.30)',
    colorFillSecondary: 'rgba(40, 36, 33, 0.40)',
    colorFillTertiary: 'rgba(40, 36, 33, 0.50)',
    colorFillQuaternary: 'rgba(40, 36, 33, 0.60)',

    colorLink: tokens.colors.accentSage,
    colorLinkHover: tokens.colors.accentGold,
    colorLinkActive: tokens.colors.accentGold,

    boxShadow: '0 12px 28px rgba(0, 0, 0, 0.20)',
    boxShadowSecondary: '0 18px 50px rgba(0, 0, 0, 0.25)',
    boxShadowTertiary: '0 4px 12px rgba(0, 0, 0, 0.15)',
  },
  components: {
    ...defaultTheme.components,
    Layout: {
      ...defaultTheme.components?.Layout,
      headerBg: tokens.colors.panelDark,
      siderBg: tokens.colors.panelDark,
      bodyBg: tokens.colors.bgDark,
      footerBg: tokens.colors.panelDark,
      colorBgTrigger: tokens.colors.lineDark,
    },
    Table: {
      ...defaultTheme.components?.Table,
      headerBg: tokens.colors.panelDarkStrong,
      rowHoverBg: 'rgba(122, 138, 106, 0.06)',
      colorBgContainer: tokens.colors.panelDarkStrong,
      borderColor: tokens.colors.lineDark,
    },
    Menu: {
      ...defaultTheme.components?.Menu,
      colorBgContainer: 'transparent',
      colorItemBgSelected: 'rgba(40, 36, 33, 0.60)',
      colorItemText: tokens.colors.mutedDark,
      colorItemTextSelected: tokens.colors.textDark,
      colorItemTextHover: tokens.colors.textDark,
      colorItemBgHover: 'rgba(40, 36, 33, 0.50)',
    },
    Card: {
      ...defaultTheme.components?.Card,
      colorBgContainer: tokens.colors.panelDarkStrong,
      colorBorderSecondary: tokens.colors.lineDark,
    },
    Input: {
      ...defaultTheme.components?.Input,
      colorBgContainer: tokens.colors.panelDark,
      colorBorder: tokens.colors.lineDark,
      hoverBorderColor: tokens.colors.lineDarkStrong,
    },
    Select: {
      ...defaultTheme.components?.Select,
      colorBgContainer: tokens.colors.panelDark,
      colorBorder: tokens.colors.lineDark,
    },
    Tag: {
      ...defaultTheme.components?.Tag,
      defaultBg: 'rgba(40, 36, 33, 0.72)',
      defaultColor: tokens.colors.mutedDark,
    },
    Skeleton: {
      ...defaultTheme.components?.Skeleton,
      color: tokens.colors.lineDark,
      colorGradientEnd: 'rgba(160, 150, 138, 0.15)',
    },
  },
};

// ─────────────────────────────────────────────────────────────
// Theme Map & Helpers
// ─────────────────────────────────────────────────────────────

export const themes: Record<string, ThemeConfig> = {
  default: defaultTheme,
  dark: darkTheme,
};

export function getTheme(name: string): ThemeConfig {
  return themes[name] || defaultTheme;
}

// ─────────────────────────────────────────────────────────────
// CSS Variables (applied to :root)
// ─────────────────────────────────────────────────────────────

export const cssVariableMap = {
  light: {
    '--ae-bg': tokens.colors.bg,
    '--ae-bg-secondary': tokens.colors.bgSecondary,
    '--ae-panel': tokens.colors.panel,
    '--ae-panel-strong': tokens.colors.panelStrong,
    '--ae-text': tokens.colors.text,
    '--ae-muted': tokens.colors.muted,
    '--ae-line': tokens.colors.line,
    '--ae-line-strong': tokens.colors.lineStrong,
    '--ae-shadow': tokens.colors.shadow,
    '--ae-shadow-soft': tokens.colors.shadowSoft,
    '--ae-accent-olive': tokens.colors.accentOlive,
    '--ae-accent-gold': tokens.colors.accentGold,
    '--ae-accent-sage': tokens.colors.accentSage,
    '--ae-success': tokens.colors.success,
    '--ae-warning': tokens.colors.warning,
    '--ae-danger': tokens.colors.danger,
    '--ae-overlay': tokens.colors.overlay,
    '--ae-radius-sm': `${tokens.radius.sm}px`,
    '--ae-radius-md': `${tokens.radius.md}px`,
    '--ae-radius-lg': `${tokens.radius.lg}px`,
    '--ae-radius-xl': `${tokens.radius.xl}px`,
    '--ae-radius-full': `${tokens.radius.full}px`,
    '--ae-motion-ease': tokens.motion.easeDefault,
    '--ae-motion-ease-smooth': tokens.motion.easeSmooth,
    '--ae-motion-duration-fast': tokens.motion.durationFast,
    '--ae-motion-duration-normal': tokens.motion.durationNormal,
    '--ae-motion-duration-slow': tokens.motion.durationSlow,
    '--ae-sidebar-width': '280px',
    '--ae-header-height': '64px',
    '--ae-content-padding': '28px',
    '--ae-font-family': tokens.typography.fontFamily,
    '--ae-font-family-serif': tokens.typography.fontFamilySerif,
    '--ae-font-family-mono': tokens.typography.fontFamilyMono,
  },
  dark: {
    '--ae-bg': tokens.colors.bgDark,
    '--ae-bg-secondary': tokens.colors.bgDarkSecondary,
    '--ae-panel': tokens.colors.panelDark,
    '--ae-panel-strong': tokens.colors.panelDarkStrong,
    '--ae-text': tokens.colors.textDark,
    '--ae-muted': tokens.colors.mutedDark,
    '--ae-line': tokens.colors.lineDark,
    '--ae-line-strong': tokens.colors.lineDarkStrong,
    '--ae-shadow': '0 18px 50px rgba(0, 0, 0, 0.25)',
    '--ae-shadow-soft': '0 12px 28px rgba(0, 0, 0, 0.15)',
    '--ae-accent-olive': '#8a9a7a',
    '--ae-accent-gold': '#d4a85a',
    '--ae-accent-sage': '#aaba98',
    '--ae-success': '#7fb08a',
    '--ae-warning': '#e0b86a',
    '--ae-danger': '#d48a7e',
    '--ae-overlay': tokens.colors.overlayDark,
    '--ae-radius-sm': `${tokens.radius.sm}px`,
    '--ae-radius-md': `${tokens.radius.md}px`,
    '--ae-radius-lg': `${tokens.radius.lg}px`,
    '--ae-radius-xl': `${tokens.radius.xl}px`,
    '--ae-radius-full': `${tokens.radius.full}px`,
    '--ae-motion-ease': tokens.motion.easeDefault,
    '--ae-motion-ease-smooth': tokens.motion.easeSmooth,
    '--ae-motion-duration-fast': tokens.motion.durationFast,
    '--ae-motion-duration-normal': tokens.motion.durationNormal,
    '--ae-motion-duration-slow': tokens.motion.durationSlow,
    '--ae-sidebar-width': '280px',
    '--ae-header-height': '64px',
    '--ae-content-padding': '28px',
    '--ae-font-family': tokens.typography.fontFamily,
    '--ae-font-family-serif': tokens.typography.fontFamilySerif,
    '--ae-font-family-mono': tokens.typography.fontFamilyMono,
  },
} as const;

export type ThemeMode = 'light' | 'dark';

export function applyCssVariables(mode: ThemeMode) {
  if (typeof document === 'undefined') return;

  const vars = cssVariableMap[mode];
  const root = document.documentElement;

  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });

  root.setAttribute('data-theme', mode);
}

// ─────────────────────────────────────────────────────────────
// Responsive helpers
// ─────────────────────────────────────────────────────────────

export const breakpoints = tokens.breakpoints;

export const mediaQueries = {
  xs: `@media (max-width: ${breakpoints.xs}px)`,
  sm: `@media (max-width: ${breakpoints.sm}px)`,
  md: `@media (max-width: ${breakpoints.md}px)`,
  lg: `@media (max-width: ${breakpoints.lg}px)`,
  xl: `@media (max-width: ${breakpoints.xl}px)`,
  xxl: `@media (max-width: ${breakpoints.xxl}px)`,
  mobile: `@media (max-width: ${breakpoints.md - 1}px)`,
  tablet: `@media (min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`,
  desktop: `@media (min-width: ${breakpoints.lg}px)`,
};
