/**
 * CADDEE Color Palette
 * Golf-themed, classic & rich aesthetic with dark green-black UI
 *
 * Design philosophy: Deep, luxurious greens inspired by championship
 * golf courses, with warm sand/gold accents for contrast and a
 * dark green-tinted background system for the UI shell.
 */

export const colors = {
  // ── Primary Greens ──────────────────────────────────────────
  /** Deep grass green — primary brand color, titles, active accents */
  primary:        '#1B6B2A',
  /** Brighter fairway green — hover states, highlighted elements */
  primaryLight:   '#2E8B3E',
  /** Darkest green — pressed states, deep emphasis */
  primaryDark:    '#145220',
  /** Putting-green surface — icon use, illustration fills */
  puttingGreen:   '#3DA550',

  // ── Secondary / Warm Accents ────────────────────────────────
  /** Sand bunker khaki — secondary buttons, tags, subtle highlights */
  sand:           '#C9B97A',
  /** Clubhouse gold — premium accents, badges, important indicators */
  gold:           '#D4AF37',
  /** Warm ivory — card surfaces, light-mode text backgrounds */
  ivory:          '#F5F0E1',

  // ── Background System (dark green-black) ────────────────────
  /** Deepest background — app shell, main canvas */
  bgBase:         '#080F0A',
  /** Panel backgrounds — sidebars, chat area, tool panels */
  bgPanel:        '#0E1A12',
  /** Elevated surfaces — cards, modals, dropdowns */
  bgElevated:     '#142318',
  /** Subtle hover/active surface */
  bgHover:        '#1A2E20',

  // ── Borders & Dividers ──────────────────────────────────────
  /** Default border — panels, inputs */
  border:         '#1E3525',
  /** Stronger border — focused inputs, active panels */
  borderStrong:   '#2A4A33',

  // ── Text ────────────────────────────────────────────────────
  /** Primary text — high contrast on dark backgrounds */
  textPrimary:    '#E8EDE9',
  /** Secondary text — descriptions, labels, timestamps */
  textSecondary:  '#8FA896',
  /** Muted text — placeholders, disabled states */
  textMuted:      '#5C7A65',

  // ── Semantic / Status ───────────────────────────────────────
  /** Success — compilation complete, connected, valid */
  success:        '#4CAF50',
  /** Warning — compiling, compatibility caution */
  warning:        '#FFB74D',
  /** Error — failures, disconnected, invalid */
  error:          '#E57373',
  /** Info — tips, neutral highlights */
  info:           '#64B5F6',

  // ── 3D Viewport ─────────────────────────────────────────────
  /** Viewport canvas background */
  viewport:       '#0E1A12',
  /** Mesh color — stable/rendered model */
  meshStable:     '#888888',
  /** Mesh color — compiling/preview state */
  meshCompiling:  '#FFB74D',

  // ── Chat Bubbles ────────────────────────────────────────────
  /** User message background */
  chatUser:       '#142E1A',
  /** AI/assistant message background */
  chatAssistant:  '#0E1A12',
  /** Error message background */
  chatError:      '#2E1A1A',
} as const;

export type ColorKey = keyof typeof colors;
