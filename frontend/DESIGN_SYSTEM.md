# TaxPilot AI — Design System

Dark, warm, cinematic fintech design system built on `#0F0703` base, `#FF6803` action orange, `#30FFAC` / `#16F456` mint-green verification accents, translucent glass surfaces, and the **Outfit** typeface.

## 1. Design Tokens (`src/styles/globals.css` & `tailwind.config.js`)

| Token | CSS Variable | Value | Usage |
|---|---|---|---|
| Base Canvas | `--bg-base` | `#0F0703` | Page background behind fixed orange glows |
| Elevated Surface | `--bg-elevated` | `#170B05` | Floating sidebar rail, top bar, modals, dropdowns |
| Surface 1 | `--surface-1` | `rgba(255, 255, 255, 0.04)` | `GlassCard` backgrounds |
| Surface 2 | `--surface-2` | `rgba(255, 255, 255, 0.07)` | Inputs, table chip rows, segmented container, secondary buttons |
| Surface 3 | `--surface-3` | `rgba(255, 255, 255, 0.10)` | Hover states, active segmented item |
| Border Subtle | `--border-subtle` | `rgba(255, 255, 255, 0.08)` | Card & input borders |
| Border Strong | `--border-strong` | `rgba(255, 255, 255, 0.16)` | Active pills, modal borders |
| Brand Orange | `--brand-orange` | `#FF6803` | Primary CTAs, active sidebar item, running pulse, chart stroke |
| Brand Amber | `--brand-amber` | `#FF8A1F` | Hover on primary CTAs, retrying status |
| Accent Mint | `--accent-mint` | `#30FFAC` | Logo mark, completed/supported status, selected bar highlight |
| Accent Green | `--accent-green` | `#16F456` | Positive metric trends |
| Text Primary | `--text-primary` | `#FFFFFF` | Headings, metric values, active labels |
| Text Secondary | `--text-secondary` | `rgba(255, 255, 255, 0.64)` | Body copy, inactive nav labels |
| Text Muted | `--text-muted` | `rgba(255, 255, 255, 0.40)` | Table headers, timestamps, captions |
| Danger | `--danger` | `#FF5A4F` | Failed, contradicted, rejected, destructive actions |
| Warning | `--warning` | `#FFB020` | Blocked, unverified, needs evidence |
| Info | `--info` | `#7DB8FF` | Parsed / informational badges (used sparingly) |

### Radii & Spacing
- Cards: `24px` (`rounded-card`)
- Inner cards, inputs, chip rows: `16px` (`rounded-inner`)
- Sidebar active item: `14px` (`rounded-nav`)
- Buttons, badges, segmented controls: `9999px` (`rounded-full`)
- Strict `4px` spacing scale: page padding `24px–32px`, card padding `24px`, grid gap `20px`.

## 2. Typography
- **Font:** `Outfit` (weights `400`, `500`, `600`) via `@fontsource/outfit` + Google Fonts fallback.
- **Monospace:** `JetBrains Mono` for GSTINs, invoice numbers, MCP/SSE logs.
- **Tabular Numerals:** `.tabular-nums` on all currency (`₹ 1,23,456.00`), GSTINs, and table amounts.

## 3. Core Components (`src/components/ui/`)
- `GlassCard` / `HeroCard`
- `Button` (`primary`, `secondary`, `white`, `ghost`, `destructive`, loading/disabled states)
- `Input` (48px height, 16px radius, orange focus ring, inline danger error, password toggle)
- `StatusBadge` (8px dot + label on 12% tinted pill; covers all investigation, agent, evidence, and role statuses)
- `SegmentedControl` & `FilterDropdown`
- `DataTable` (uppercase 12px headers, 16px rounded `surface-2` chip rows with 8px gap)
- `EmptyState`, `ErrorState`, `Skeleton` / `SkeletonCard` / `SkeletonRow`
- `ConfirmationModal`, `Avatar`, `Breadcrumbs`, `PageHeader`
