---
name: eFootball Arena
colors:
  # Backgrounds
  surface: "#0A0F1A"
  surface-dim: "#060B14"
  surface-bright: "#161e2e"
  surface-container-lowest: "#050A12"
  surface-container-low: "#0E1321"
  surface-container: "#111827"
  surface-container-high: "#161e2e"
  surface-container-highest: "#1F2937"
  on-surface: "#F3F4F6"
  on-surface-variant: "#9CA3AF"
  inverse-surface: "#F3F4F6"
  inverse-on-surface: "#111827"
  outline: "#374151"
  outline-variant: "rgba(255, 255, 255, 0.06)"
  surface-tint: "#106EBE"
  # Primary — Steel Blue (main action colour)
  primary: "#106EBE"
  on-primary: "#FFFFFF"
  primary-container: "rgba(16, 110, 190, 0.15)"
  on-primary-container: "#60AAED"
  inverse-primary: "#1581e0"
  # Secondary — Electric Teal (highlight / vibe colour)
  secondary: "#0FFCBE"
  on-secondary: "#0A0F1A"
  secondary-container: "rgba(15, 252, 190, 0.12)"
  on-secondary-container: "#0FFCBE"
  # Tertiary — reserved for future brand extension
  tertiary: "#60A5FA"
  on-tertiary: "#0A0F1A"
  tertiary-container: "rgba(96, 165, 250, 0.12)"
  on-tertiary-container: "#60A5FA"
  # Semantic
  error: "#EF4444"
  on-error: "#FFFFFF"
  error-container: "rgba(239, 68, 68, 0.12)"
  on-error-container: "#EF4444"
  # Warning
  warning: "#F59E0B"
  on-warning: "#0A0F1A"
  warning-container: "rgba(245, 158, 11, 0.12)"
  on-warning-container: "#F59E0B"
  # Glassmorphism overlay
  glass-surface: "rgba(17, 24, 39, 0.90)"
  glass-border: "rgba(255, 255, 255, 0.06)"
  # Page background
  background: "#0A0F1A"
  on-background: "#F3F4F6"
  surface-variant: "#1F2937"

typography:
  # Display — hero headlines, score readouts (Orbitron)
  display-lg:
    fontFamily: Orbitron
    fontSize: 72px
    fontWeight: "900"
    lineHeight: 80px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Orbitron
    fontSize: 48px
    fontWeight: "900"
    lineHeight: 56px
    letterSpacing: -0.01em
  display-sm:
    fontFamily: Orbitron
    fontSize: 36px
    fontWeight: "800"
    lineHeight: 44px
    letterSpacing: -0.01em
  # Headlines — section titles, card headings (Orbitron)
  headline-lg:
    fontFamily: Orbitron
    fontSize: 24px
    fontWeight: "800"
    lineHeight: 32px
    letterSpacing: 0.05em
  headline-md:
    fontFamily: Orbitron
    fontSize: 18px
    fontWeight: "700"
    lineHeight: 26px
    letterSpacing: 0.05em
  # Body — general UI copy (Inter)
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 20px
  # Labels — nav links, badges, button text (Inter)
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: "700"
    lineHeight: 20px
    letterSpacing: 0.08em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: "700"
    lineHeight: 16px
    letterSpacing: 0.08em
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: "800"
    lineHeight: 14px
    letterSpacing: 0.1em

rounded:
  none: 0
  sm: 0.5rem
  DEFAULT: 0.75rem
  md: 0.75rem
  lg: 0.875rem
  xl: 1.5rem
  full: 9999px

spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 80px
  card-padding: 24px
  section-gap: 48px
  navbar-height: 95px
  navbar-height-scrolled: 75px
  container-padding: 20px

elevation:
  # All surfaces are dark; depth is expressed through alpha layers and glow.
  0: "none"
  1: "0 8px 32px rgba(0, 0, 0, 0.30)"
  2: "0 10px 25px rgba(0, 0, 0, 0.40)"
  3: "0 10px 40px rgba(0, 0, 0, 0.50)"
  glow-primary: "0 0 20px rgba(16, 110, 190, 0.15)"
  glow-secondary: "0 0 15px rgba(15, 252, 190, 0.30)"
  glow-hover: "0 8px 24px rgba(16, 110, 190, 0.40)"

motion:
  duration-fast: "200ms"
  duration-default: "300ms"
  duration-slow: "600ms"
  easing-default: "cubic-bezier(0.4, 0, 0.2, 1)"
  easing-spring: "cubic-bezier(0.16, 1, 0.3, 1)"
  easing-bounce: "cubic-bezier(0.175, 0.885, 0.32, 1.275)"
  page-enter: "pageFadeIn 500ms ease-out forwards"
  card-stagger-delay: "50ms"

components:
  # Glassmorphism card — the primary surface container
  glass-card:
    backgroundColor: "{colors.surface-container}"
    borderColor: "rgba(255, 255, 255, 0.05)"
    borderWidth: 1px
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.card-padding}"
    backdropFilter: "blur(24px) saturate(180%)"
    shadow: "{elevation.1}"
  glass-card-hover:
    borderColor: "rgba(255, 255, 255, 0.10)"

  # Primary button — bold filled blue, used for main CTAs
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.sm}"
    padding: "0.75rem 2rem"
    shadow: "none"
    textTransform: uppercase
    letterSpacing: 0.08em
  button-primary-hover:
    backgroundColor: "{colors.inverse-primary}"
    shadow: "{elevation.glow-hover}"
    transform: "scale(1.02)"

  # Outline ghost button — secondary action
  button-outline:
    backgroundColor: "transparent"
    textColor: "#FFFFFF"
    borderColor: "{colors.outline-variant}"
    borderWidth: 1px
    typography: "{typography.label-lg}"
    rounded: "{rounded.sm}"
    padding: "0.75rem 2rem"
  button-outline-hover:
    borderColor: "{colors.secondary}"
    textColor: "{colors.secondary}"
    transform: "scale(1.02)"

  # Danger ghost button — destructive actions
  button-danger:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
    borderColor: "rgba(239, 68, 68, 0.20)"
    borderWidth: 1px
    typography: "{typography.label-lg}"
    rounded: "{rounded.sm}"
    padding: "0.75rem 2rem"
  button-danger-hover:
    backgroundColor: "{colors.error}"
    textColor: "#FFFFFF"
    shadow: "0 8px 24px rgba(239, 68, 68, 0.40)"

  # Frosted navbar
  navbar:
    backgroundColor: "{colors.glass-surface}"
    backdropFilter: "blur(24px) saturate(180%)"
    borderBottomColor: "{colors.glass-border}"
    borderBottomWidth: 1px
    height: "{spacing.navbar-height}"
  navbar-scrolled:
    backgroundColor: "rgba(10, 15, 26, 0.95)"
    height: "{spacing.navbar-height-scrolled}"
    shadow: "{elevation.3}"

  # Nav links
  nav-link:
    textColor: "rgba(255, 255, 255, 0.60)"
    typography: "{typography.label-md}"
    rounded: "{rounded.sm}"
    padding: "0.6rem 0.75rem"
  nav-link-hover:
    textColor: "#FFFFFF"
    backgroundColor: "rgba(255, 255, 255, 0.04)"
  nav-link-active:
    textColor: "{colors.secondary}"

  # Logo mark — gradient icon pill
  logo-icon:
    size: 38px
    background: "linear-gradient(135deg, {colors.primary}, {colors.secondary})"
    rounded: 10px
    shadow: "0 0 15px rgba(15, 252, 190, 0.30)"

  # Profile pill (authenticated user)
  profile-pill:
    backgroundColor: "rgba(255, 255, 255, 0.05)"
    borderColor: "{colors.glass-border}"
    borderWidth: 1px
    rounded: "{rounded.full}"
    padding: "6px 16px"
  profile-pill-hover:
    backgroundColor: "rgba(255, 255, 255, 0.10)"
    borderColor: "{colors.secondary}"
    shadow: "0 0 15px rgba(15, 252, 190, 0.10)"

  # Badge — tournament / application status chips
  badge:
    typography: "{typography.label-sm}"
    padding: "4px 10px"
    rounded: 6px
  badge-ongoing:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.primary}"
    borderColor: "rgba(16, 110, 190, 0.20)"
  badge-registration:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.secondary}"
    borderColor: "rgba(15, 252, 190, 0.20)"
  badge-completed:
    backgroundColor: "rgba(255, 255, 255, 0.05)"
    textColor: "#FFFFFF"
    borderColor: "{colors.outline-variant}"
  badge-pending:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    borderColor: "rgba(245, 158, 11, 0.20)"
  badge-approved:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
  badge-rejected:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
    borderColor: "rgba(239, 68, 68, 0.20)"

  # Stat box — numeric KPI tiles on homepage & admin
  stat-box:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline-variant}"
    borderWidth: 1px
    rounded: "{rounded.sm}"
    padding: "{spacing.card-padding}"
    textAlign: center
  stat-box-number:
    fontFamily: Orbitron
    fontSize: 28px
    fontWeight: "900"
    textColor: "#FFFFFF"
  stat-box-label:
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-variant}"

  # Data table
  table-header:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.label-sm}"
    padding: "1rem"
    borderBottomColor: "{colors.outline-variant}"
    borderBottomWidth: 2px
  table-cell:
    padding: "1rem"
    borderBottomColor: "{colors.outline-variant}"
    borderBottomWidth: 1px
  table-row-hover:
    backgroundColor: "rgba(255, 255, 255, 0.02)"

  # Form fields
  input-field:
    backgroundColor: "{colors.surface-container-low}"
    borderColor: "#1F2937"
    borderWidth: 1px
    textColor: "#FFFFFF"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: "0.75rem 1rem"
  input-field-focus:
    borderColor: "{colors.secondary}"
    shadow: "0 0 0 3px rgba(15, 252, 190, 0.10)"
  form-label:
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    marginBottom: "0.5rem"

  # Position rank badge (leaderboard / standings)
  position-badge-1:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    fontFamily: Orbitron
    size: 28px
    rounded: 4px
  position-badge-2:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
  position-badge-3:
    backgroundColor: "#F3F4F6"
    textColor: "{colors.on-secondary}"
  position-badge-default:
    backgroundColor: "rgba(255, 255, 255, 0.05)"
    textColor: "{colors.on-surface-variant}"

  # Score display (match result)
  score-display:
    fontFamily: Orbitron
    fontSize: 64px
    fontWeight: "900"
    textColor: "#FFFFFF"
  score-vs:
    fontFamily: Orbitron
    fontSize: 20px
    fontWeight: "900"
    textColor: "{colors.secondary}"

  # Mobile bottom navigation bar
  mobile-bottom-nav:
    backgroundColor: "rgba(10, 15, 25, 0.85)"
    backdropFilter: "blur(24px)"
    borderTopColor: "rgba(255, 255, 255, 0.05)"
    borderTopWidth: 1px
    height: 65px

  # Toast / notification
  toast:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.primary}"
    rounded: "{rounded.DEFAULT}"

  # Alert messages (Django messages framework)
  alert:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline-variant}"
    borderLeftColor: "{colors.primary}"
    borderLeftWidth: 4px
    rounded: "{rounded.sm}"
    textColor: "{colors.on-surface}"

  # Empty state
  empty-state-icon:
    fontSize: 56px
    textColor: "{colors.on-surface-variant}"
    opacity: 0.3
  empty-state-title:
    typography: "{typography.headline-md}"
    textColor: "#FFFFFF"
  empty-state-text:
    typography: "{typography.body-md}"
    textColor: "{colors.on-surface-variant}"
    maxWidth: 400px

  # Footer
  footer:
    backgroundColor: "{colors.surface-container-low}"
    borderTopColor: "{colors.outline-variant}"
    borderTopWidth: 1px
    padding: "4rem 0 2rem"
---

## Brand & Style

**eFootball Arena** is a competitive e-football tournament management platform. Its visual identity is built around the aesthetics of premium esports — dark, data-rich, energetic, and authoritative.

The design style is **Cyberpunk Glassmorphism meets Military-Grade Data Dashboard**. Every surface is deep navy-black, cards are frosted with backdrop blur, and two complementary accent colours — Steel Blue for actions and Electric Teal for highlights — create a vibrant tension against the near-black background. Typography mixes the geometric, futuristic **Orbitron** typeface for all headings and numeric displays with **Inter** for all body copy and UI labels, creating a clear split between "match data" and "explanatory text."

The platform targets competitive gamers who expect a premium, immersive experience equivalent to watching a live sports broadcast. The interface should feel like a war room: precise, cinematic, alive.

---

## Colors

The palette is intentionally minimal and highly saturated against a very dark background.

- **Background (`#0A0F1A`):** Near-black with a blue cast — colder than pure black, evoking a night-time stadium environment.
- **Card surface (`#111827`):** One step lighter; creates the layer separation needed for the glassmorphism effect without breaking the dark mood.
- **Primary — Steel Blue (`#106EBE`):** The action colour. Used for primary CTAs, active nav links, alert left-borders, and the logo gradient start. Conveys trust, precision, and authority.
- **Secondary — Electric Teal (`#0FFCBE`):** The vibe colour. Used sparingly for active nav indicators, badge highlights, leaderboard first-place accents, focus states, and hover borders. Its high chroma creates an almost neon glow against the dark background that reads as "live" and "competitive."
- **Error — Vermilion Red (`#EF4444`):** Danger actions, destructive states, rejected badges, and pending-result warnings.
- **Warning — Amber (`#F59E0B`):** Pending-team badges and attention-drawing admin metrics.
- **Text Primary (`#F3F4F6`):** Off-white, never pure white; reduces eye strain on dark backgrounds.
- **Text Secondary / Muted (`#9CA3AF`):** Used for descriptive copy, timestamps, and table meta-labels — always subordinate to primary text.

Never use solid white `#FFFFFF` as a background. All glass surfaces must use the defined `rgba` alpha values so the dark background bleeds through.

---

## Typography

Two font families are used — this dual-family system is fundamental to the brand.

### Orbitron — "The Arena Voice"
Used for **everything that communicates match data or identity**: H1–H6 headings, section titles, score displays, stat numbers, position badges, the navbar brand name, and all `.font-orbitron` utilities. Orbitron's angular, monospaced DNA evokes digital scoreboards and military targeting systems. It must always appear **uppercase or title-case** — never sentence case.

- Hero titles: `font-size: clamp(2.5rem, 6vw, 4.5rem)`, `font-weight: 900`, `letter-spacing: -1px`
- Section titles: `font-size: 1.5rem`, `font-weight: 800`, `text-transform: uppercase`, `letter-spacing: 1px`
- Score display: `font-size: 4rem`, `font-weight: 900`

### Inter — "The Analyst's Voice"
Used for **all explanatory and interactive text**: body paragraphs, nav links, button labels, form labels, table cells, badge text, toast messages, and metadata. Inter's neutrality and exceptional legibility balance Orbitron's aggression.

- Body: `font-weight: 400`, `line-height: 1.6`
- Nav links: `font-size: 0.8rem`, `font-weight: 700`, `text-transform: uppercase`, `letter-spacing: 1px`
- Form labels: `font-size: 0.75rem`, `font-weight: 600`, `text-transform: uppercase`, `letter-spacing: 1px`

Both families should always be rendered with `-webkit-font-smoothing: antialiased` for crispness on dark backgrounds.

---

## Layout & Spacing

The layout uses Bootstrap 5's 12-column grid as a structural skeleton, customised heavily via CSS variables and utility overrides.

- **Base unit:** 8px. All spacing values are multiples thereof.
- **Navbar:** Fixed, 95px tall (collapses to 75px on scroll). `main` receives a `100px` top padding to clear it.
- **Home hero:** Full-bleed section that handles its own top padding (`120px 0`). The body class `is-home` disables the default main padding.
- **Card gap:** `1.5rem` (24px) between grid cards; internal card padding is also `1.5rem`.
- **Section separation:** `py-5` (48px) between major page sections.
- **Mobile bottom nav:** Fixed 65px bar replaces the top nav on `≤768px`. Body receives `padding-bottom: 80px` to compensate.
- **Horizontal scroll snap:** On mobile, card grids switch to `scroll-snap-type: x mandatory` with 85% card width for a swipe-based experience.

---

## Elevation & Depth

Depth is conveyed entirely through **alpha layering and glow**, not lightness. The background is the darkest point; every layer above it must be fractionally lighter.

### Layer Stack (bottom to top)
1. **Page background:** `#0A0F1A` — the void.
2. **Navbar / footers:** `rgba(14, 19, 33, 0.90)` + `backdrop-filter: blur(24px) saturate(180%)` — frosted, floating above the page.
3. **Glass cards:** `#111827` + `border: 1px solid rgba(255,255,255,0.05)` + `box-shadow: 0 8px 32px rgba(0,0,0,0.30)` — the primary content layer.
4. **Dropdowns / toasts:** Same glass treatment with an additional `border: 1px solid glass-border`.
5. **HTMX loading overlay:** `z-index: 2000` — always on top.

### Glow Effect
Interaction states express themselves through **coloured glow shadows**, not solid fills:
- Primary hover: `box-shadow: 0 8px 24px rgba(16, 110, 190, 0.40)`
- Logo icon: `box-shadow: 0 0 15px rgba(15, 252, 190, 0.30)`
- Active nav underline: `box-shadow: 0 0 10px #0FFCBE`
- Focus ring: `box-shadow: 0 0 0 3px rgba(15, 252, 190, 0.10)`

---

## Shapes

The shape language is **sharp but not harsh** — rounded enough to feel modern, rectangular enough to signal precision.

- **Cards, modals, dropdowns:** `border-radius: 12px` (desktop) / `8px` (mobile ≤768px).
- **Buttons, form inputs, small chips:** `border-radius: 8px` (desktop) / `6px` (mobile).
- **Profile pill / navbar user menu toggle:** `border-radius: 9999px` — the only fully rounded element, making it visually distinct as a personal identity element.
- **Position rank badges:** `border-radius: 4px` — intentionally angular to read like a military rank insignia.
- **Avatar initials circle:** `border-radius: 50%`.
- **Logo icon:** `border-radius: 10px` — slightly softer than cards.

---

## Motion & Animation

Motion is functional and cinematic. Every animation should feel like a broadcast transition, not a cute loading spinner.

### Page Enter
```
@keyframes pageFadeIn {
  from { opacity: 0; filter: blur(10px); }
  to   { opacity: 1; filter: blur(0); }
}
duration: 500ms, easing: ease-out
```
Applied to `body` on every page load for a broadcast-style reveal.

### Content Stagger
All direct children of `main > .container` receive `fadeInUp` animations with cascaded delays (`50ms`, `100ms`, `150ms`…). This creates a waterfall effect as the page settles.
```
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
duration: 600ms, easing: cubic-bezier(0.16, 1, 0.3, 1)
```

### Goal Celebration
When a match result is confirmed, the score element briefly pulses with a cyan glow:
```
@keyframes goalCelebrate {
  0%   { transform: scale(1);    box-shadow: 0 0  0px rgba(0,255,255, 0.0); }
  50%  { transform: scale(1.05); box-shadow: 0 0 40px rgba(0,255,255, 0.4); }
  100% { transform: scale(1);    box-shadow: 0 0  0px rgba(0,255,255, 0.0); }
}
duration: 800ms, easing: cubic-bezier(0.175, 0.885, 0.32, 1.275)
```

### Button & Interactive Element Transitions
All interactive elements use `all 0.2s cubic-bezier(0.4, 0, 0.2, 1)` (the Material Design standard easing) as the default. Button hover adds `transform: scale(1.02)`; active states snap back with `transform: scale(0.98)`.

### HTMX Loading
During HTMX requests, `body.opacity` drops to `0.7` and pointer events are suppressed (`pointer-events: none`) with a `0.3s ease` transition, signalling to the user that a network action is in flight without a disruptive spinner.

---

## Key UI Patterns

### The Glass Card
The most important surface element. Do not use plain white or grey cards.
```
background: #111827
border: 1px solid rgba(255,255,255,0.05)
border-radius: 12px
padding: 1.5rem
backdrop-filter: blur(24px)
box-shadow: 0 8px 32px rgba(0,0,0,0.30)
```
On hover, the border lightens to `rgba(255,255,255,0.10)` — a subtle acknowledgement without breaking the glass illusion.

### Accent-Coloured Section Titles
Section titles always use Orbitron, are ALL CAPS, and split the title word between the default white and the Electric Teal accent:
```
ACTIVE <span class="text-accent">LEAGUES</span>
```
This two-tone split is a signature visual rhythm across the platform.

### Status Badges
Status chips are always rendered with a translucent background tinted to match the semantic colour, a matching coloured border, and coloured text — never a solid opaque fill (except `badge-approved`, which uses the solid Electric Teal background as a "green light" signal).

### Navbar Active Indicator
The active page nav link glows in Electric Teal with an animated underline pseudo-element:
```css
color: #0FFCBE
::after { background: #0FFCBE; box-shadow: 0 0 10px #0FFCBE; height: 2px; }
```

### Text Selection
Text selection uses the secondary teal at 25% alpha, keeping the brand colour present even in passive interactions:
```css
::selection { background: rgba(15, 252, 190, 0.25); color: #fff; }
```

### Scrollbar
Custom scrollbar using a dark thumb (`#1c222d`) with a 2px border matching the page background to create a floating-bar effect. Thumb turns Steel Blue on hover.

---

## Responsive Behaviour

| Breakpoint | Changes |
|---|---|
| `≤992px` | Hero font scales down to `3rem` |
| `≤768px` | Radii shrink (`12px → 8px`, `8px → 6px`); mobile bottom nav appears; top nav hides; body adds bottom padding; full-width buttons |
| `≤576px` | Hero font `2rem`; score display `2rem`; reduced gap utilities |

The mobile bottom nav provides quick access to Home, Standings, Transfer Hub, and My Team. It uses the same frosted glass treatment as the top navbar (`rgba(10, 15, 25, 0.85)` + `backdrop-filter: blur(24px)`).

---

## Iconography

All icons are sourced from **Font Awesome 6** (Free tier), rendered inline with `<i>` tags. Icons never stand alone — they always accompany text labels in navigation and buttons. Semantic colour-coding is applied:
- Teal (`.text-accent-2`): Section header icons, primary info icons.
- Amber (`.text-warning`): Warning states, pending items.
- Red (`.text-danger`): Error states, logout, destructive actions.
- Muted grey: Empty state icons at 30% opacity.
