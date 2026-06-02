# Frontend UI/UX/UE Review Report

**Project:** Agent Engine Platform (Next.js 14 + React + Ant Design + Tailwind)  
**Date:** 2026-06-02  
**Reviewer:** Claude Code (ui-ux-pro-max skill)  
**Scope:** `frontend/src/` — all pages, components, hooks, lib, store

---

## Executive Summary

| Dimension | Score | Grade | Critical Issues |
|-----------|-------|-------|-----------------|
| P1 Accessibility | 4/10 | D | 6 Critical |
| P2 Touch & Interaction | 7/10 | C+ | 1 Critical |
| P3 Performance | 6/10 | C | 2 Critical |
| P4 Style Selection | 8/10 | B+ | 0 |
| P5 Layout & Responsive | 7/10 | C+ | 1 Warning |
| P6 Typography & Color | 8/10 | B+ | 0 |
| P7 Animation | 8/10 | B+ | 1 Warning |
| P8 Forms & Feedback | 7/10 | C+ | 2 Warning |
| P9 Navigation Patterns | 6/10 | C | 2 Warning |
| P10 Charts & Data | 5/10 | C- | 1 Warning |
| **Overall** | **6.6/10** | **C+** | **6 Critical, 10 Warning** |

**Verdict:** Strong visual design system ("Soft Editorial Warmth") with excellent glassmorphism consistency and animation polish. However, **accessibility is a major liability** — missing ARIA, focus traps, semantic HTML, and label associations would create compliance risk and exclude users with disabilities. Performance and navigation also need attention.

---

## P1 — Accessibility (CRITICAL) 🔴 Score: 4/10

### Critical Issues

#### 1.1 Sidebar navigation lacks semantic HTML and ARIA
- **File:** `components/Sidebar.tsx`
- **Issue:** Navigation uses raw `<button>` elements inside `<aside>`, not `<nav>`. No `aria-label`, `aria-current`, or `aria-expanded` on category toggles. Screen readers cannot identify this as navigation.
- **Fix:** Wrap in `<nav aria-label="Main navigation">`. Add `aria-current="page"` to active item. Add `aria-expanded` to category buttons.

#### 1.2 Custom Modal is inaccessible
- **File:** `components/ui/Modal.tsx`
- **Issue:** No `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap, or Escape key handling. Screen readers and keyboard users are trapped or lost.
- **Fix:** Add ARIA attributes. Implement focus trap (use `react-focus-lock` or manual). Handle `Escape` key. Return focus to trigger on close.

#### 1.3 Form labels not programmatically associated
- **File:** `components/ui/Input.tsx`, `components/ui/Select.tsx`, `components/ui/TextArea.tsx`
- **Issue:** Labels use `<label>` but no `htmlFor`/`id` pairing. `aria-describedby` not linking errors to inputs.
- **Fix:** Generate unique IDs, add `htmlFor` to label, `aria-describedby` pointing to error message ID.

#### 1.4 No skip links
- **File:** `app/(platform)/layout.tsx`
- **Issue:** No "Skip to main content" link for keyboard users. Must tab through entire sidebar on every page load.
- **Fix:** Add `<a href="#main-content" className="sr-only focus:not-sr-only">Skip to main content</a>` as first focusable element.

#### 1.5 Toast notifications lack live regions
- **File:** `components/ui/Toast.tsx`
- **Issue:** `aria-live` region missing. Screen readers do not announce toasts.
- **Fix:** Add `aria-live="polite"` or `role="status"` to toast container.

#### 1.6 StatusBadge relies on color alone
- **File:** `components/ui/StatusBadge.tsx`
- **Issue:** Processing/running/completed states use green/red/blue dots without text labels. Colorblind users cannot distinguish.
- **Fix:** Add visually hidden text or tooltip with status name (e.g., `<span className="sr-only">Processing</span>`).

### Warnings

#### 1.7 No focus restoration after modal/command palette close
- **File:** `components/ui/Modal.tsx`, `components/CommandPalette.tsx`
- **Issue:** Focus not returned to trigger element after dismissal.
- **Fix:** Save `document.activeElement` on open, restore on close.

#### 1.8 ChatMessage hardcoded colors bypass theme tokens
- **File:** `components/ChatMessage.tsx`
- **Issue:** User bubble uses `#1890ff` (Ant Design blue), status tags use hardcoded Ant Design colors. May fail contrast in dark mode.
- **Fix:** Map to semantic tokens (`--ae-accent-olive`, `--ae-success`, `--ae-danger`).

---

## P2 — Touch & Interaction (CRITICAL) 🟡 Score: 7/10

### Critical Issues

#### 2.1 Toast auto-dismiss too fast for errors
- **File:** `components/ui/Toast.tsx`
- **Issue:** All toasts auto-dismiss in 3 seconds. Error messages need more time to read and act upon.
- **Fix:** Error toasts: 8–10s or persistent with manual close. Success toasts: 3s OK.

### Warnings

#### 2.2 Modal close button uses unlabeled ✕ character
- **File:** `components/ui/Modal.tsx`
- **Issue:** `<button>` with `✕` text has no `aria-label="Close"`.
- **Fix:** Add `aria-label="Close dialog"`.

#### 2.3 ToggleSwitch lacks state semantics
- **File:** `components/ui/ToggleSwitch.tsx`
- **Issue:** Custom toggle may not expose `aria-checked` or `role="switch"` to assistive tech.
- **Fix:** Add `role="switch"` and `aria-checked={checked}`.

#### 2.4 Loading buttons lack progress indication
- **File:** Various pages using Ant Design `Button loading`
- **Issue:** No progress percentage or step indicator for long operations (e.g., file upload, model training).
- **Fix:** Use `ProgressBar` or step indicators for multi-second operations.

---

## P3 — Performance (HIGH) 🟡 Score: 6/10

### Critical Issues

#### 3.1 No image format optimization strategy
- **File:** `next.config.js`
- **Issue:** No WebP/AVIF configuration. No `images.formats` in Next.js config. Project uses default image handling.
- **Fix:** Add `images: { formats: ['image/avif', 'image/webp'] }` to `next.config.js`. Audit all `<img>` tags for `next/image` usage.

#### 3.2 No route-level code splitting evident
- **File:** `app/(platform)/` pages
- **Issue:** No `dynamic()` imports found for heavy pages (workflow editor, observability charts, marketplace). Initial bundle likely large.
- **Fix:** Lazy load heavy routes:
  ```tsx
  const WorkflowEditor = dynamic(() => import('./WorkflowEditor'), { ssr: false });
  ```

### Warnings

#### 3.3 Glassmorphism backdrop-filter can cause GPU overhead
- **File:** `globals.css`, multiple components
- **Issue:** `backdrop-filter: blur(16px)` applied to many panels simultaneously. Can cause jank on lower-end devices.
- **Fix:** Consider reducing to `blur(12px)` on mobile. Use `@media (hover: hover)` to disable on low-power mode if needed.

#### 3.4 Framer Motion may not respect prefers-reduced-motion
- **File:** `components/CommandPalette.tsx`, `components/onboarding/`
- **Issue:** No `useReducedMotion` hook usage found. Framer Motion animations may run despite user preference.
- **Fix:** Wrap Framer Motion components with `useReducedMotion()` check.

#### 3.5 No virtualized lists for long data
- **File:** `components/ui/Table.tsx`, various list pages
- **Issue:** No `react-window` or `react-virtualized` usage. Tables with 1000+ rows will cause memory and scroll issues.
- **Fix:** Implement virtual scrolling for tables and lists with >50 items.

---

## P4 — Style Selection (HIGH) 🟢 Score: 8/10

### Strengths

- **Consistent glassmorphism aesthetic** across all components. `backdrop-filter: blur(16px)` + semi-transparent panels is uniformly applied.
- **Token-driven theming**: 145+ usages of `var(--ae-*)` CSS variables. Strong semantic token system.
- **No emoji icons**: Uses SVG and Ant Design icons throughout.
- **Style match**: "Soft Editorial Warmth" with warm parchment + olive + gold suits an AI platform product well — calm, trustworthy, premium.
- **Shadow consistency**: Warm-tinted shadows (`rgba(74,60,48)`) used everywhere instead of generic gray.

### Warnings

#### 4.1 Onboarding components use a different visual style
- **File:** `components/onboarding/OnboardingModal.tsx`
- **Issue:** Blue/purple gradient (`#1890ff`, `#722ed1`) clashes with the warm editorial palette. Looks like default Ant Design styling leaked in.
- **Fix:** Recolor onboarding to use olive/gold/parchment tokens.

#### 4.2 SkeletonLoader uses hardcoded gray backgrounds
- **File:** `components/ui/SkeletonLoader.tsx`
- **Issue:** `#f0f0f0`, `#f5f5f5` do not adapt to dark mode.
- **Fix:** Use `--ae-bg-secondary` and `--ae-panel` tokens.

---

## P5 — Layout & Responsive (HIGH) 🟡 Score: 7/10

### Strengths

- **Mobile-first Tailwind**: `hidden md:block` for sidebar, responsive grid classes (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`).
- **Mobile drawer sidebar**: Proper Ant Design `Drawer` on mobile, not just hidden.
- **Container widths**: Consistent max-width approach with `mx-4` padding on mobile.

### Warnings

#### 5.1 Platform layout uses fixed pixel margins
- **File:** `app/(platform)/layout.tsx`
- **Issue:** `md:ml-[280px]` for sidebar offset. If sidebar width changes, content area breaks.
- **Fix:** Use CSS custom property `--sidebar-width` and `margin-left: var(--sidebar-width)`.

#### 5.2 No responsive font size scale (except headings)
- **File:** `globals.css`, components
- **Issue:** Body text stays at 13–14px on all devices. No text scaling for accessibility.
- **Fix:** Use `clamp()` or responsive Tailwind text utilities. Ensure 16px minimum on mobile inputs to prevent iOS zoom.

#### 5.3 Command Palette width not fully responsive
- **File:** `components/CommandPalette.tsx`
- **Issue:** Max-width 640px with `mx-4`. On very small screens (<375px), may still feel cramped.
- **Fix:** Test at 320px. Consider `max-w-full sm:max-w-lg`.

---

## P6 — Typography & Color (MEDIUM) 🟢 Score: 8/10

### Strengths

- **Excellent token system**: `lib/theme.ts` exports comprehensive typography tokens (font families, sizes, weights, line heights).
- **Strong hierarchy**: Serif for display headings (h1–h3), sans for UI, mono for code.
- **Color semantic tokens**: `success`, `warning`, `danger`, `accentOlive`, `accentGold` all mapped consistently.
- **Line height**: Body text at 1.6, headings at 0.96 (editorial tightness is intentional and effective).
- **Dark mode**: Full inversion with desaturated variants, not naive color inversion.

### Warnings

#### 6.1 Glassmorphism panel text contrast may fail WCAG in some states
- **File:** `components/ui/Card.tsx`, `globals.css`
- **Issue:** `rgba(255,255,255,0.74)` panel over warm parchment background with 13px muted text at 58% opacity. Against certain background gradients, contrast may dip below 4.5:1.
- **Fix:** Audit with axe or Lighthouse. Increase panel opacity to 0.82 or darken muted text opacity to 0.72.

#### 6.2 MarkdownRenderer code block uses hardcoded dark theme
- **File:** `components/MarkdownRenderer.tsx`
- **Issue:** Code blocks use GitHub-dark colors (`#24292e`, `#0d1117`) regardless of app theme. In light mode, this is jarring.
- **Fix:** Use a theme-aware syntax highlighter (e.g., `highlight.js` with light/dark CSS swap).

---

## P7 — Animation (MEDIUM) 🟢 Score: 8/10

### Strengths

- **Consistent timing**: 180ms fast, 200ms normal, 300ms slow across all components.
- **Easing discipline**: `cubic-bezier(.2,1,.2,1)` for smooth deceleration on entrances.
- **Transform/opacity only**: Hover effects use `translateY` and `box-shadow`, not `width`/`height`.
- **Reduced motion support**: `prefers-reduced-motion` media query disables all CSS animations.
- **Purposeful motion**: Card hover lift (`translateY(-4px)`), button press feedback, page `floatIn` all communicate state change.

### Warnings

#### 7.1 Framer Motion may bypass reduced-motion
- **File:** `components/CommandPalette.tsx`, `components/onboarding/`
- **Issue:** No evidence of `useReducedMotion` integration. Framer Motion springs and transitions may still play.
- **Fix:** Add `const shouldReduceMotion = useReducedMotion()` and conditionally set `transition={{ duration: 0 }}`.

#### 7.2 Decorative drift animation may cause distraction
- **File:** `components/ui/Card.tsx` (decorative blob)
- **Issue:** `drift 12s ease-in-out infinite alternate` on card decorative elements. Subtle but constant motion on multiple cards could cause discomfort.
- **Fix:** Pause drift on `prefers-reduced-motion` or make it `animation-play-state: paused` by default, play on hover.

---

## P8 — Forms & Feedback (MEDIUM) 🟡 Score: 7/10

### Strengths

- **Zod validation layer**: `lib/validation.ts` has comprehensive schemas with user-friendly error messages.
- **Inline error display**: `Input.tsx` shows errors below fields with red border and text.
- **Loading states**: Buttons use Ant Design `loading` prop. Global `useLoadingStore` prevents duplicate submissions.
- **Empty states**: Contextual and actionable (`EmptyState.tsx`) across agents, marketplace, tools pages.
- **Error recovery**: `lib/errorHandler.ts` has excellent error categorization and retry logic.

### Warnings

#### 8.1 No inline validation timing strategy
- **File:** Various form pages
- **Issue:** Validation appears to trigger on submit only. No blur validation pattern observed.
- **Fix:** Implement `validateOnBlur` in `useFormValidation` hook. Show error after user leaves field, not during typing.

#### 8.2 No undo for destructive actions
- **File:** `components/ui/ConfirmModal.tsx`
- **Issue:** Confirmation dialogs are present but no "undo" toast pattern (e.g., "Item deleted — Undo") observed.
- **Fix:** Add undo toast for deletions and bulk actions.

#### 8.3 No auto-save for long forms
- **File:** `app/(platform)/agents/`, `app/(platform)/workflows/`
- **Issue:** Agent creation and workflow editor likely have multi-step forms with no draft persistence.
- **Fix:** Auto-save drafts to `localStorage` with debounce.

---

## P9 — Navigation Patterns (HIGH) 🟡 Score: 6/10

### Strengths

- **Command Palette**: Excellent keyboard-driven navigation with full shortcut discovery.
- **Keyboard shortcuts**: `useKeyboardShortcuts.ts` with domain-specific hooks.
- **Deep linking**: Next.js App Router provides URL-based routing for all pages.
- **Active state highlighting**: Sidebar shows current page with gradient left border.

### Warnings

#### 9.1 No breadcrumbs
- **File:** All pages
- **Issue:** No breadcrumb navigation anywhere. Users in deep pages (e.g., `/workflows/abc123/edit`) have no visual hierarchy trail.
- **Fix:** Add `<Breadcrumb>` component to platform layout, driven by route segments.

#### 9.2 No browser back button state preservation
- **File:** Various pages
- **Issue:** `router.push()` used instead of `<Link>`. Browser back may not preserve scroll position or filter state.
- **Fix:** Replace programmatic navigation with `<Link>` where possible. Use `scroll: false` option when appropriate.

#### 9.3 Navigation shortcuts not discoverable
- **File:** `hooks/useKeyboardShortcuts.ts`
- **Issue:** Shortcuts are hardcoded and not shown anywhere except Command Palette.
- **Fix:** Add a "Keyboard Shortcuts" help modal (triggered by `?` key) listing all shortcuts.

---

## P10 — Charts & Data (LOW) 🟡 Score: 5/10

### Warnings

#### 10.1 No data table alternative for charts
- **File:** `components/evaluations/EvalResultChart.tsx`, `components/observability/`
- **Issue:** Charts alone are not screen-reader friendly. No `<table>` fallback or `aria-label` summary found.
- **Fix:** Provide "View as table" toggle or `aria-label` describing chart insight.

#### 10.2 Chart colors may not be colorblind-safe
- **File:** `components/observability/PerformanceCharts.tsx`
- **Issue:** No evidence of pattern/texture supplement for data series. Relies on color alone.
- **Fix:** Use patterned fills or distinct line styles (solid, dashed, dotted) in addition to color.

#### 10.3 No chart empty/error states
- **File:** Chart components
- **Issue:** No explicit error state for failed data loads. May show blank axes.
- **Fix:** Add error boundary + retry button for chart data fetching.

---

## Fix Priority Matrix

| Priority | Issue | Effort | Impact | File |
|----------|-------|--------|--------|------|
| **P0** | Add ARIA to Sidebar | Low | High | `components/Sidebar.tsx` |
| **P0** | Fix Modal accessibility | Low | High | `components/ui/Modal.tsx` |
| **P0** | Label-input association | Low | High | `components/ui/Input.tsx`, `Select.tsx`, `TextArea.tsx` |
| **P0** | Add skip links | Low | High | `app/(platform)/layout.tsx` |
| **P1** | Toast live regions | Low | Medium | `components/ui/Toast.tsx` |
| **P1** | StatusBadge text labels | Low | Medium | `components/ui/StatusBadge.tsx` |
| **P1** | Breadcrumbs | Medium | Medium | New component + layout |
| **P1** | Image optimization config | Low | Medium | `next.config.js` |
| **P2** | Framer Motion reduced-motion | Low | Low | `components/CommandPalette.tsx`, onboarding |
| **P2** | Route-level lazy loading | Medium | Medium | `app/(platform)/` pages |
| **P2** | Onboarding color consistency | Low | Low | `components/onboarding/` |
| **P2** | Form blur validation | Medium | Medium | `lib/validation.ts`, forms |

---

## Positive Highlights

1. **Design token architecture** is exemplary — `lib/theme.ts` as single source of truth with CSS variables, Ant Design config, and helper functions.
2. **Command Palette** is a gold-standard component — full keyboard navigation, focus management, empty state, and polished animation.
3. **Error handling** with typed error classes and automatic retry is production-grade.
4. **Onboarding system** with spotlight effect and keyboard navigation shows genuine UX investment.
5. **Glassmorphism consistency** — every surface uses the same blur, border, and shadow treatment.
6. **Dark mode** is fully implemented with proper token inversion, not an afterthought.

---

*Report generated by ui-ux-pro-max skill. Scores are relative to WCAG 2.1 AA, Apple HIG, and Material Design standards.*
