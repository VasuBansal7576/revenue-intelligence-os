# Causal Deal Intelligence Design System

## 1. Atmosphere & Identity

A dense revenue command desk, built for managers who need evidence before opinion. The signature is an answer-first evidence spine: the first viewport explains what changed, why it matters, and what to do next, while timestamped Memory and Knowledge records remain one step away.

## 2. Color

### Palette

| Role | Token | Light | Dark | Usage |
|------|-------|-------|------|-------|
| Surface/primary | --surface-primary | #F4F1EA | #10110F | Main app background |
| Surface/secondary | --surface-secondary | #FFFFFF | #171816 | Panels |
| Surface/elevated | --surface-elevated | #F9F7F0 | #20211F | Rows and graph nodes |
| Text/primary | --text-primary | #171816 | #F4F1EA | Main copy |
| Text/secondary | --text-secondary | #62665F | #B9BDB3 | Captions |
| Text/tertiary | --text-tertiary | #878B82 | #7E8378 | Muted metadata |
| Border/default | --border-default | #D8D2C5 | #30332D | Panel and row borders |
| Border/subtle | --border-subtle | #E8E3D8 | #242721 | Quiet dividers |
| Accent/primary | --accent-primary | #315F8C | #78A6C8 | Links and focus |
| Accent/secondary | --accent-secondary | #7A4F2B | #D09B6A | Production status and warnings |
| Status/success | --status-success | #315D45 | #79B68E | Healthy deal signals |
| Status/warning | --status-warning | #8A641D | #D8B35A | Medium risk |
| Status/error | --status-error | #8C352F | #D77770 | High risk |
| Status/info | --status-info | #315F8C | #78A6C8 | Informational signals |

### Rules

- Accent colors are semantic, never decorative.
- Production status uses `--accent-secondary` everywhere it appears.
- No surface uses shadows; hierarchy comes from tone and borders.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| H1 | 28px | 700 | 1.2 | 0 | Product title |
| H2 | 20px | 650 | 1.3 | 0 | Panel title |
| H3 | 16px | 650 | 1.4 | 0 | Row title |
| Body | 14px | 400 | 1.55 | 0 | Default text |
| Body/sm | 13px | 400 | 1.45 | 0 | Dense panel content |
| Caption | 12px | 550 | 1.35 | 0 | Metadata and labels |
| Mono | 12px | 500 | 1.4 | 0 | Node ids and timestamps |

### Font Stack

- Primary: Arial, Helvetica, system-ui, sans-serif
- Mono: SFMono-Regular, Consolas, Liberation Mono, monospace

### Rules

- Body text never drops below 12px because this is a dense operator surface.
- Node ids and timestamps use the mono scale.

## 4. Spacing & Layout

### Base Unit

All spacing derives from a base of 4px.

| Token | Value | Usage |
|-------|-------|-------|
| --space-1 | 4px | Hairline gaps |
| --space-2 | 8px | Inline groups |
| --space-3 | 12px | Dense row padding |
| --space-4 | 16px | Panel padding |
| --space-5 | 20px | Header spacing |
| --space-6 | 24px | Main gutters |
| --space-8 | 32px | Large section gaps |

### Grid

- Max content width: none; this is a full-width console.
- Desktop: answer strip, compact replay band, full-width cited briefing, then progressive proof trail.
- Tablet/mobile: panels stack in source order.
- Breakpoints: sm 640px, md 768px, lg 1024px, xl 1280px.

### Rules

- Panels fill the viewport height on desktop.
- Repeated rows use fixed internal spacing to prevent layout jumps.

## 5. Components

### App Frame

- **Structure**: header, mode badge, tenant metadata, answer strip, compact replay band, cited briefing, proof disclosures.
- **Spacing**: `--space-4`, `--space-5`, `--space-6`.
- **States**: production status always visible.
- **Accessibility**: semantic header and main landmarks.
- **Motion**: none.

### Panel

- **Structure**: section with panel header and scrollable body.
- **Variants**: timeline, briefing.
- **Spacing**: `--space-4`.
- **States**: focus outline on links and buttons.
- **Accessibility**: labelled by visible heading.
- **Motion**: none.

### Evidence Row

- **Structure**: title, metadata, signal badges, summary.
- **Variants**: call, memory, knowledge.
- **Spacing**: `--space-3`, `--space-4`.
- **States**: hover tonal shift.
- **Accessibility**: ids remain visible as text.
- **Motion**: 120ms color transition.

### Signal Badge

- **Structure**: short text label inside a bordered span.
- **Variants**: success, warning, error, info, production.
- **Spacing**: `--space-1`, `--space-2`.
- **States**: none.
- **Accessibility**: never color-only; text carries the meaning.
- **Motion**: none.

### Graph Node

- **Structure**: node label, node id, confidence or status metadata.
- **Variants**: deal, contact, call, causal link.
- **Spacing**: `--space-3`.
- **States**: hover tonal shift.
- **Accessibility**: causal edges rendered as text rows below the visual grouping.
- **Motion**: none.

### Proof Disclosure

- **Structure**: native details/summary with short metadata, title, and one-line summary.
- **Variants**: graph, call timeline, evidence inspector.
- **Spacing**: `--space-4`.
- **States**: closed by default for secondary proof; graph may open by default when it explains the active answer.
- **Accessibility**: native disclosure semantics and keyboard operation.
- **Motion**: none.

## 6. Motion & Interaction

### Timing

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro | 120ms | ease-out | Hover and focus tone changes |
| Standard | 200ms | ease-in-out | Future panel reveal |

### Rules

- Only color, transform, and opacity may transition.
- Respect `prefers-reduced-motion`.
- No layout animations in the console shell.

## 7. Depth & Surface

### Strategy

Borders-only.

| Type | Value | Usage |
|------|-------|-------|
| Default | 1px solid var(--border-default) | Panels and rows |
| Subtle | 1px solid var(--border-subtle) | Internal separators |
