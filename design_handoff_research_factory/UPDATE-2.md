# Research Factory — design update for Claude Code

Apply to the existing implementation. The prototype files in this bundle are already updated —
`git diff -- design_handoff_research_factory/` shows the exact source changes; this file is the
intent. Nothing else about the design changed.

## Round 2 (this update)

1. **Theme toggle is back in the top bar.** Right side order is now:
   `"N repros ready" pill · light/dark toggle · join-the-waitlist CTA`.
   Same behavior as before: button label shows the mode you'd switch TO ("light mode" while
   dark, "dark mode" while light); flips `data-pf-theme` on `<html>`; persists to
   `localStorage["pf-theme"]`; applied pre-paint. The live/poll chip and sign-in button stay
   removed.

2. **Dark-theme surfaces brightened: anything white in light mode is now dark grey in dark
   mode** (clear separation from the `#0C1013` canvas). Exact token changes in `:root`
   (`pf.css`) — light values unchanged:

   | token | old dark | new dark | used by |
   |---|---|---|---|
   | `--pf-panel` | `#0E1418` | `#182027` | table panel, workflow panel, loop cards' halo/label bg |
   | `--pf-surface` | `#11171B` | `#182027` | repro panel, attempt cards, decided/note blocks |
   | `--pf-surface-2` | `#161E23` | `#1E272E` | review action bar |
   | `--pf-panel-h` | `#0F1418` | `#141B21` | pane headers (ABSTRACT / GENERATED), logo tile |
   | `--pf-field` | `#0F1519` | `#161D24` | search input, form inputs, checklist rows |
   | `--pf-hover` | `#141B20` | `#1F282F` | table row hover |
   | `--pf-bar` | `#1A2328` | `#252F37` | score-bar track |
   | `--pf-track` | `#26333A` | `#2C3840` | slider track |

   Unchanged on purpose: `--pf-canvas #0C1013`, `--pf-topbar #0A0E11`, and the always-dark
   code/terminal zones (`--pf-code #090D10`, `--pf-term #06090B`) — code blocks stay darker
   than their surrounding panels in both themes.

## Round 1 (verify these already landed)

1. Top bar reduced to: logo tile · factory/settings tabs · repros-ready pill · waitlist CTA.
2. Self-healing loops simplified: loop 1 has no return arrow/label; both loops' legend rows
   and bottom notes removed; loop 2 titled "loop 2 — the generated reproduction broke" and
   keeps only its dashed retry arc + "on failure, retry with the traceback, max 2".
3. Table sits on a bordered panel: `background: var(--pf-panel); border: 1px solid
   var(--pf-line-2)` (white card in light mode, now dark-grey card in dark mode per Round 2).
4. HOW IT WORKS is the 4-step rail (scrape / score / reproduce / monitoring & review) under
   that title, with "SELF HEALING LOOPS" as the loops header.
