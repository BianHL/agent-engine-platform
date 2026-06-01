/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Brand Accents
        olive: {
          DEFAULT: 'var(--ae-accent-olive)',
          light: 'var(--ae-accent-sage)',
        },
        gold: {
          DEFAULT: 'var(--ae-accent-gold)',
        },
        sage: {
          DEFAULT: 'var(--ae-accent-sage)',
        },
        // Backgrounds
        parchment: {
          DEFAULT: 'var(--ae-bg)',
          deep: 'var(--ae-bg-secondary)',
        },
        // Panels (glassmorphism)
        panel: {
          DEFAULT: 'var(--ae-panel)',
          strong: 'var(--ae-panel-strong)',
        },
        // Text
        ink: {
          DEFAULT: 'var(--ae-text)',
          muted: 'var(--ae-muted)',
        },
        // Semantic
        success: {
          DEFAULT: 'var(--ae-success)',
        },
        warning: {
          DEFAULT: 'var(--ae-warning)',
        },
        danger: {
          DEFAULT: 'var(--ae-danger)',
        },
        // Borders
        line: {
          DEFAULT: 'var(--ae-line)',
          strong: 'var(--ae-line-strong)',
        },
        overlay: 'var(--ae-overlay)',
      },
      fontFamily: {
        sans: ['var(--ae-font-family)', 'system-ui', 'sans-serif'],
        serif: ['var(--ae-font-family-serif)', 'Georgia', 'serif'],
        mono: ['var(--ae-font-family-mono)', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        sm: 'var(--ae-radius-sm)',
        md: 'var(--ae-radius-md)',
        lg: 'var(--ae-radius-lg)',
        xl: 'var(--ae-radius-xl)',
        full: 'var(--ae-radius-full)',
      },
      boxShadow: {
        card: 'var(--ae-shadow)',
        soft: 'var(--ae-shadow-soft)',
        button: '0 14px 28px rgba(168, 149, 106, 0.18)',
        'focus-ring': '0 0 0 3px rgba(122, 138, 106, 0.12)',
      },
      transitionTimingFunction: {
        smooth: 'var(--ae-motion-ease-smooth)',
      },
      transitionDuration: {
        fast: 'var(--ae-motion-duration-fast)',
        normal: 'var(--ae-motion-duration-normal)',
        slow: 'var(--ae-motion-duration-slow)',
      },
      spacing: {
        'ae-xs': '4px',
        'ae-sm': '8px',
        'ae-md': '12px',
        'ae-lg': '16px',
        'ae-xl': '20px',
        'ae-2xl': '24px',
        'ae-3xl': '28px',
      },
      maxWidth: {
        prose: '65ch',
        content: '1200px',
      },
      backdropBlur: {
        panel: '16px',
      },
    },
  },
  plugins: [],
  corePlugins: {
    // We keep preflight disabled because Ant Design provides its own base styles
    // and we don't want conflicts. Our globals.css provides the necessary reset.
    preflight: false,
  },
};
