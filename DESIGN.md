---
name: Agent Engine Platform
description: Enterprise-grade AI agent orchestration and operations platform.
colors:
  background: "#f5efe6"
  background-secondary: "#ece3d6"
  panel: "rgba(255, 255, 255, 0.74)"
  panel-strong: "rgba(255, 255, 255, 0.92)"
  text-primary: "#26221e"
  text-muted: "rgba(38, 34, 30, 0.58)"
  border: "rgba(86, 68, 54, 0.10)"
  border-strong: "rgba(86, 68, 54, 0.18)"
  shadow: "0 18px 50px rgba(74, 60, 48, 0.10)"
  shadow-soft: "0 12px 28px rgba(74, 60, 48, 0.06)"
  accent-olive: "#7a8a6a"
  accent-gold: "#c29a63"
  accent-sage: "#9aaa88"
  success: "#6f9b7c"
  warning: "#d0a45d"
  danger: "#c47a6e"
  danger-secondary: "#cf7c73"
  dark-bg: "#1c1917"
  dark-bg-secondary: "#252220"
  dark-panel: "rgba(40, 36, 33, 0.74)"
  dark-panel-strong: "rgba(40, 36, 33, 0.92)"
  dark-text: "#e8e2da"
  dark-muted: "rgba(232, 226, 218, 0.58)"
  dark-border: "rgba(160, 150, 138, 0.10)"
  dark-border-strong: "rgba(160, 150, 138, 0.18)"
typography:
  sans:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    usage: "Body text, UI elements, labels, buttons, form inputs"
  serif:
    fontFamily: "ui-serif, Georgia, Cambria, 'Times New Roman', serif"
    usage: "Display headings, hero titles, stat values, editorial accents"
rounded:
  xl: "30px"
  lg: "22px"
  md: "16px"
  sm: "12px"
  full: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
  3xl: "28px"
---

# Design System: Agent Engine Platform

## 1. Overview

**Creative North Star: "The Well-Typeset Workshop"**

Agent Engine's interface should feel like a warm, well-lit workshop table covered with carefully arranged tools and materials — not a sterile lab, not a flashy showroom. Every surface has a purpose; every color earns its place; every animation whispers rather than shouts.

The aesthetic is **soft editorial warmth** — warm stone neutrals that feel like aged paper and parchment, olive-green and warm-gold accents that evoke natural materials rather than digital signals, and generous spacing that lets the eye rest between information clusters. This is an interface designed for 6-hour work sessions, not 30-second demos.

We explicitly reject: default Ant Design blue themes, high-contrast dark SaaS dashboards, neon AI aesthetics, cold gray enterprise UIs, glassmorphism without purpose, and gradient text.

### Theme Rationale: Light Mode as Default

**Scene**: ML engineers and platform operators in well-lit office environments, configuring agents and reviewing observability dashboards for extended sessions. Natural or overhead lighting, large monitors at arm's length.

Light mode is the correct default because:
- **Eye strain**: Warm beige surfaces (`#f5efe6`) reflect ambient light naturally, reducing the harsh contrast of pure white or dark screens in bright environments.
- **Color accuracy**: Low-saturation semantic colors (muted olive, warm gold, soft red) render consistently across monitors without the distortion that dark mode can introduce.
- **Information density**: Semi-transparent panels (`backdrop-filter: blur`) create depth without heavy shadows, supporting dense UIs that don't feel suffocating.
- **Professional context**: Enterprise operators expect tool interfaces to feel like paper and ink, not cinema screens.

**Dark mode** is available as a user preference (toggle in the header), not the default. It preserves the warm tone — dark surfaces are tinted toward warm charcoal (`#1c1917`) rather than cold pure black.

### Spacing Application Guide

**Base Unit**: 8px. Most spacing values are multiples of 8px, with smaller 4px increments for tight internal gaps.

**Spacing Scale & Usage:**
- **4px (xs)**: Icon-to-text gap, inline element gaps, tight padding (chips, tags, badges)
- **8px (sm)**: Related element gaps (nav items, tag groups, form field internals)
- **12px (md)**: Button padding vertical, card footer gaps, compact card padding
- **16px (lg)**: Standard card body padding, section element gaps, form field gaps
- **20px (xl)**: Hero card internal gaps, action button groups
- **24px (2xl)**: Section separation, page content padding, sidebar internal padding
- **28px (3xl)**: Large card padding (hero, feature cards), topbar padding

**Rhythm Rules:**
1. **Related elements**: Smaller spacing (4px–8px) shows visual grouping
2. **Unrelated elements**: Larger spacing (16px–24px) shows separation
3. **Section breaks**: 24px–32px indicates major content transitions
4. **Consistency**: Same relationship = same spacing everywhere
5. **Generosity**: When in doubt, add more space. The interface should breathe.

### Motion & Animation

**Easing Curves:**
- **Default**: `ease` — Used for most hover states and simple transitions
- **Smooth deceleration**: `cubic-bezier(.2,1,.2,1)` — For entrance animations (floatIn)
- **Infinite drift**: `ease-in-out` — For decorative ambient animations

**Duration Scale:**
- **180ms–200ms**: Standard transitions (hover states, background changes, opacity, border-color)
- **250ms–300ms**: Content transitions (tab switches, modal appear/disappear)
- **400ms**: Toast entrance/exit
- **650ms**: Page-level entrance animations (card floatIn)
- **12s**: Decorative ambient animations (gradient drift)

**Motion Rules:**
- Never animate layout properties (width, height, margin, padding). Use `transform` and `opacity` only.
- Respect `prefers-reduced-motion: reduce`. All animations degrade to instant state changes.
- No bounce, no elastic easing. Deceleration and smooth transitions only.
- Decorative motion should be subtle and ambient (slow drift), never attention-grabbing.

## 2. Colors

The palette is built on a warm parchment neutral foundation with olive-green and warm-gold accents. Every color is tinted warm — there are no pure blacks, no cold grays, no blue undertones.

### Backgrounds
- **Warm Parchment** (`#f5efe6` oklch(95% 0.01 75)): Primary page background. Like high-quality unbleached paper.
- **Warm Parchment Deep** (`#ece3d6` oklch(92% 0.01 75)): Secondary background for gradients, inset surfaces, sidebar backgrounds.
- **Panel White** (`rgba(255, 255, 255, 0.74)`): Glassmorphism panel background. Semi-transparent white with `backdrop-filter: blur(16px)`.
- **Panel White Strong** (`rgba(255, 255, 255, 0.92)`): More opaque panel for content-heavy surfaces.

### Text
- **Primary Text** (`#26221e` oklch(20% 0.01 60)): Headings, body text, interactive labels. Warm-tinted near-black.
- **Muted Text** (`rgba(38, 34, 30, 0.58)`): Secondary text, metadata, captions, descriptions, placeholders.

### Accents
- **Olive Green** (`#7a8a6a` oklch(65% 0.05 135)): Primary accent. Used for active nav states, success indicators, primary chip dots, focus rings. A muted, natural green that feels organic rather than digital.
- **Warm Gold** (`#c29a63` oklch(72% 0.1 80)): Secondary accent. Used for primary buttons, gradient endpoints, progress bars, star ratings. The warm heartbeat of the interface.
- **Sage Green** (`#9aaa88` oklch(72% 0.04 135)): Tertiary accent. Used for gradient midpoints, hover states, subtle highlights.

### Semantic Colors
- **Success Green** (`#6f9b7c` oklch(68% 0.06 145)): Healthy states, positive confirmations. Slightly more saturated than Olive Green to indicate vitality.
- **Warning Gold** (`#d0a45d` oklch(74% 0.1 82)): Caution states, processing indicators. Brighter than Warm Gold to draw attention.
- **Danger Red** (`#c47a6e` oklch(62% 0.08 30)): Errors, destructive actions. Warm-tinted red that harmonizes with the palette rather than clashing.

### Borders & Dividers
- **Subtle Border** (`rgba(86, 68, 54, 0.10)`): Default card borders, section separators.
- **Strong Border** (`rgba(86, 68, 54, 0.18)`): Active states, hovered borders, emphasis separators.

### Shadows
- **Card Shadow** (`0 18px 50px rgba(74, 60, 48, 0.10)`): Elevated cards, modals. Warm-tinted, not pure black.
- **Soft Shadow** (`0 12px 28px rgba(74, 60, 48, 0.06)`): Subtle elevation for nav items, dropdowns.
- **Button Shadow** (`0 14px 28px rgba(168,149,106,.18)`): Primary button elevation. Tinted toward gold.

### Dark Mode Palette
When `data-theme="dark"` is set on `<html>`:
- **Background**: `#1c1917` (warm charcoal)
- **Background Secondary**: `#252220` (warm charcoal light)
- **Panel**: `rgba(40, 36, 33, 0.74)` (warm dark glass)
- **Panel Strong**: `rgba(40, 36, 33, 0.92)`
- **Text**: `#e8e2da` (warm off-white)
- **Muted**: `rgba(232, 226, 218, 0.58)`
- **Borders**: `rgba(160, 150, 138, 0.10)` and `(0.18)`
- All accent colors shift slightly warmer/lighter for visibility on dark surfaces

### Named Color Rules
**The No Pure Black/White Rule.** `#000000` and `#ffffff` are prohibited. Even our "white" panels are semi-transparent and tinted. Dark mode backgrounds are warm charcoal, not pure black. This maintains tonal harmony across the entire palette.

**The Warm Tint Rule.** Every neutral color has a warm undertone (toward orange/brown, not blue/gray). Shadows are warm brown, not cold gray. Text is warm black, not pure black.

## 3. Typography

**Primary Font (Sans-serif)**: Inter (with system-ui fallback) — Used for all UI elements, body text, labels, buttons, form inputs.

**Display Font (Serif)**: Georgia / ui-serif — Used for page titles, hero headings, stat values, and editorial accents. The serif/display pairing creates the "soft editorial" feel.

**Character**: Inter provides technical precision and excellent readability at small sizes. Georgia adds warmth and gravitas to large headings. The combination feels like a well-designed technical journal — precise body text paired with expressive headlines.

### Hierarchy
- **Display** (Serif, 700 weight, clamp(38px, 4.2vw, 58px), line-height 0.96): Page titles. Letter-spacing: -0.04em. Max-width: 12ch.
- **Headline** (Serif, 700 weight, clamp(32px, 3.6vw, 52px), line-height 0.98): Section hero headings, card hero titles. Letter-spacing: -0.05em.
- **Title** (Sans, 700 weight, 16px, line-height 1.2): Card titles, list item names. Letter-spacing: -0.02em.
- **Body** (Sans, 400 weight, 15px, line-height 1.75): Primary reading text, descriptions. Max-width: 64ch.
- **Label** (Sans, 600 weight, 12px–13px, line-height 1.4, letter-spacing 0.12em–0.18em): Uppercase labels, eyebrow text, section headers, stat labels. Always uppercase with generous letter-spacing.
- **Small** (Sans, 400 weight, 12px–13px, line-height 1.55): Metadata, captions, timestamps, badge text.

### Named Typography Rules
**The Serif-for-Display Rule.** Serif fonts are reserved for display-size headings (24px+). All UI text, buttons, labels, form elements, and body text use sans-serif exclusively. Never use serif for buttons, nav items, or form labels.

**The Tight Display Rule.** Display and headline text uses negative letter-spacing (-0.03em to -0.05em) for a refined, editorial feel. Body and label text use normal or positive letter-spacing.

## 4. Elevation & Surfaces

Agent Engine uses a **glassmorphism-by-default** surface strategy. Most cards and panels are semi-transparent white (`rgba(255,255,255,0.74)`) with `backdrop-filter: blur(16px)`, allowing the warm background gradients to subtly show through. This creates depth without heavy shadows.

### Surface Types
- **Glass Panel** (`rgba(255,255,255,0.74)` + `backdrop-filter: blur(16px)`): Default for cards, sidebars, dropdowns. Creates depth through transparency and blur.
- **Glass Panel Strong** (`rgba(255,255,255,0.92)` + `backdrop-filter: blur(16px)`): For content-heavy surfaces where readability is critical.
- **Gradient Background**: Pages use layered radial and linear gradients to create ambient warmth. Not flat — always has subtle depth through gradient variation.
- **Pure Surface** (`#ffffff` at opacity): Used sparingly for elements that must be fully opaque (inputs, buttons).

### Depth Indicators
- **Border**: 1px solid `var(--line)` — The primary depth indicator. Almost all elevated surfaces have a subtle border.
- **Shadow**: Used for hover states and true spatial separation (modals). Cards get `var(--shadow-soft)` on hover.
- **Gradient Overlay**: Decorative radial gradients on cards create localized depth (light spots that suggest surface curvature).

### Decorative Backgrounds
- **Page Background**: Layered radial gradients (olive, gold, sage at low opacity) + linear gradient from `--bg` to `--bg-2`.
- **Grid Overlay**: Subtle 34px grid lines at very low opacity (`rgba(86, 68, 54, 0.028)`) with mask gradient fading toward the bottom.
- **Card Decorations**: Rotated gradient shapes, radial gradient spots, and border accents that add visual interest without clutter.

### Named Elevation Rules
**The Glassmorphism Default Rule.** Surfaces are glassmorphic by default. Pure opaque white is the exception, not the rule. This creates the signature warm, layered aesthetic.

**The Gradient Decoration Rule.** Decorative gradients (rotated shapes, radial spots) are permitted on hero cards and feature surfaces. They should use palette colors at very low opacity (≤0.16) and never compete with content for attention.

## 5. Iconography

### Icon Style
- **Source**: Unicode symbols and geometric shapes (⌁, ◌, ↗, ◫, ◎) used inline, or Lucide/Phosphor icons when available.
- **Style**: Outline (stroke-based) for consistency.
- **Stroke width**: 1.5px default.
- **Size scale**: 16px (inline), 20px (default), 22px (nav icons), 24px (feature highlights).
- **Color**: Inherits from text color. Olive green for active states.

### Icon Container (Nav Icons)
- Size: 22px × 22px
- Border-radius: 8px
- Background: `rgba(126, 143, 122, 0.12)` (subtle olive tint)
- Hover: Slightly darker background, subtle scale transform

### Icon Usage Rules
1. **Consistency**: Same icon for same action across all screens.
2. **Labeling**: Icons without text labels must have `aria-label`.
3. **Sizing**: Icon size matches surrounding text scale.
4. **States**: Icons inherit hover/focus/active states from parent.

## 6. Responsive Design

### Breakpoints
| Breakpoint | Width | Layout Behavior |
|------------|-------|-----------------|
| **Mobile** | < 780px | Single column, sidebar hidden or drawer, stacked cards, reduced padding |
| **Tablet** | 780px – 1200px | Sidebar collapses or stacks above content, 2-column grids |
| **Desktop** | 1200px+ | Full sidebar (280px), 3-column card grids, standard spacing |

### Grid System
- **Page layout**: Sidebar (280px) + Content (1fr)
- **Card grid**: 12-column grid with 12px gutters
- **Stats grid**: 2×2 grid within hero section

### Responsive Rules
1. **Sidebar**: At < 1200px, sidebar moves above content. At < 780px, sidebar padding reduces to 16px.
2. **Cards**: Grid column span changes (4 → 6 → 12) at breakpoints.
3. **Typography**: Display sizes reduce by ~20% on mobile (h2: 34px fixed below 780px).
4. **Spacing**: Content padding reduces from 28px to 16px on mobile.
5. **Topbar**: Stacks vertically on tablet; search becomes full-width.

## 7. Components

### Component State Matrix

Every interactive component must implement all applicable states:

| State | Visual Change | Behavior |
|-------|---------------|----------|
| **Default** | Base appearance per component spec | Interactive |
| **Hover** | translateY(-1px), background shift, border-color shift, subtle shadow | Cursor: pointer |
| **Focus** | Border shifts to accent color, subtle glow ring | Keyboard accessible |
| **Active/Pressed** | Deeper background shift | Immediate feedback |
| **Disabled** | Muted background and text, no shadow | Cursor: not-allowed |

### Buttons
- **Shape:** Rounded corners (14px–16px radius). No fully rounded pill buttons except for chips/tags.
- **Primary:** Linear gradient background (`#b8956a` → `#a08060` → `#8b9a6d`), white text, no border. Padding: 12px 16px. Font: Sans, 13px, weight 600. Shadow: `0 14px 28px rgba(168,149,106,.18)`.
- **Hover / Focus:** translateY(-1px), border-color darkens, shadow deepens. Transition: all 180ms ease.
- **Secondary / Ghost:** Semi-transparent white background (`rgba(255,255,255,0.58)`–`0.72`), dark text, 1px border (`var(--line-strong)`). Hover: more opaque background, darker border.
- **Danger:** Danger red background or border, white/dark text. Hover: darker red.
- **Disabled:** Muted background and text. No shadow.

### Chips / Tags / Pills
- **Style:** Fully rounded (`999px` radius). Background: `rgba(255,255,255,0.72)` with 1px border. Text: muted color.
- **Active / Strong:** Text uses `var(--text)` (bold/strong inside).
- **Note Pills:** Smaller padding (9px 12px), muted text with bold keywords.

### Cards / Containers
- **Corner Style:** Large radius — 30px for feature cards, 22px for medium cards, 16px–18px for compact cards.
- **Background:** Glassmorphism gradient (`linear-gradient(180deg, rgba(255,255,255,0.82), rgba(252,250,247,0.66))`) + `backdrop-filter: blur(16px)`.
- **Shadow Strategy:** Soft shadow at rest (`var(--shadow-soft)`). Elevated shadow on hover (`var(--shadow)` with translateY).
- **Border:** 1px solid `var(--line)`. All cards have borders.
- **Internal Padding:** 28px for hero cards, 18px for standard cards, 14px–16px for compact cards.
- **Hover:** translateY(-5px for asset cards, -2px for timeline items), border-color shifts toward accent, shadow deepens.

### Inputs / Fields
- **Style:** 1px `var(--line)` border, 14px radius, glass panel background. Padding: 12px 14px.
- **Focus:** Border shifts to accent color (`var(--accent)`). Subtle glow: `0 0 0 3px rgba(122,138,106,.12)`.
- **Error:** Border shifts to danger. Error text below: 12px, danger color.
- **Disabled:** Muted background and text.

### Navigation
- **Sidebar:** 280px width, sticky positioning. Background: glassmorphism gradient. Padding: 28px 20px.
- **Menu Items:** Border-radius 16px, padding 13px 14px. Background: semi-transparent white. Active: left 3px gradient accent bar (olive to gold), stronger background, subtle shadow.
- **Hover:** translateX(2px), brighter background, subtle shadow.
- **Header:** Integrated into topbar. Right-aligned: search, theme toggle, notifications, user avatar.

### Search / Command
- **Style:** Border-radius 18px. Padding: 14px 16px. Glassmorphism background + backdrop-filter.
- **Shadow:** `var(--shadow)` (elevated).
- **Contents:** Keyboard shortcut hint (⌘K), input field, action label (kbd tag).

### Tables
- **Header:** Uppercase label style, muted color, 500 weight. Bottom border: `var(--line)`.
- **Rows:** Glass panel background. Bottom border: `var(--line)`. Hover: subtle olive tint background.
- **Cells:** 13px body text. Padding: 12px 16px.
- **Status in Tables:** Compact status badges (smaller font) within cells.

### Modals / Drawers
- **Corner Style:** 30px radius (largest in system).
- **Overlay:** `rgba(0,0,0,.35)` with `backdrop-filter: blur(4px)`.
- **Shadow:** `var(--shadow)`.
- **Header:** Serif headline, close button (32px square, border).
- **Body:** 14px muted text, form elements.
- **Footer:** Right-aligned buttons.
- **Animation:** Overlay fades in (300ms), modal scales up from 0.97 + translateY(20px) to normal.

### Status Badges
- **Style:** Inline-flex, rounded pill, small padding (6px 12px). Dot indicator (7px) with colored glow shadow.
- **Success:** Olive green dot. Glow: `rgba(111,155,124,.15)`.
- **Warning:** Gold dot. Glow: `rgba(208,164,93,.15)`.
- **Danger:** Red dot. Glow: `rgba(196,122,110,.15)`.
- **Info:** Olive dot. Glow: `rgba(122,138,106,.15)`.
- **Processing:** Pulsing gold dot (animation: pulse 1.5s ease-in-out infinite).

### Tooltips
- **Style:** Positioned above element. Padding: 6px 12px. Border-radius: 10px.
- **Background:** `var(--text)` (warm black). Text: `var(--bg)` (warm parchment). Font: 12px.
- **Animation:** Fade in + translateY shift (200ms).

### Toast Notifications
- **Container:** Fixed top-right. Flex column, gap 10px.
- **Style:** Border-radius 16px. Glass panel strong + shadow. Min-width: 280px.
- **Animation:** Slide in from right (400ms cubic-bezier). Auto-dismiss after 3s.
- **Types:** Success (checkmark icon), Error (X icon), Warning (! icon).

### Toggle Switches
- **Track:** 44px × 24px, border-radius 999px. Background: `var(--line)` when off, `var(--accent)` when on.
- **Thumb:** 20px circle, white, shadow. Slides 20px on toggle.
- **Animation:** 200ms ease transform.

### Empty States
- **Layout:** Centered content within card. Padding: 48px 28px.
- **Border:** Dashed `var(--line-strong)` instead of solid.
- **Elements:** Icon (64px gradient container), serif headline, muted description, primary CTA button.

### Progress Bars
- **Track:** 8px height, border-radius 999px. Background: `rgba(45,43,40,.07)`.
- **Fill:** Border-radius inherit. Gradient: `linear-gradient(90deg, var(--accent), var(--accent-3), var(--accent-2))`.

## 8. Do's and Don'ts

### Do:
- **Do** use warm neutrals for 90% of the interface. Color (olive, gold) is reserved for signal and action.
- **Do** use serif fonts for display headings (24px+). They add editorial warmth.
- **Do** use glassmorphism (backdrop-filter + semi-transparent backgrounds) as the default surface treatment.
- **Do** use large border radii (16px–30px) for cards. The softness matches the warm palette.
- **Do** use generous spacing. Let the interface breathe.
- **Do** use decorative gradients on hero/feature cards at very low opacity (≤0.16).
- **Do** use subtle grid overlays on page backgrounds for texture.
- **Do** ensure every interactive element has visible focus states.
- **Do** respect `prefers-reduced-motion`.

### Don't:
- **Don't** use blue or purple anywhere in the interface. The palette is strictly warm (beige, olive, gold, warm red).
- **Don't** use pure black (`#000`) or pure white (`#fff`). Everything is tinted warm.
- **Don't** use gradient text (`background-clip: text`). Emphasis through weight, size, or serif choice only.
- **Don't** use side-stripe borders (colored left borders on cards) except for sidebar nav active indicators.
- **Don't** use the hero-metric template (big number + small label + gradient) on dashboards. Metrics should be integrated into the information architecture.
- **Don't** create identical card grids with icon + heading + text repeated endlessly.
- **Don't** use decorative motion that doesn't convey state. No bouncing, no parallax.
- **Don't** use cold gray shadows. All shadows are warm-tinted.
- **Don't** nest cards inside cards. One level maximum.
- **Don't** use sans-serif for large display headings. That's what the serif font is for.
