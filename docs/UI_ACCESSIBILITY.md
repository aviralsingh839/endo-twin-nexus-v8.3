# ENDO-TWIN NEXUS — Accessibility Standard

Scope: the visual-accessibility layer of every surface this repository ships.
Covers **colour contrast, text scaling, focus visibility, motion, reflow and
non-colour status communication**. Screen-reader and keyboard semantics are
improved where they were free to add, but they are not the contract below.

Two rules govern every change:

1. **Nothing is communicated by colour alone.** A severity, provenance label or
   status is always carried by a word, a glyph or a border pattern as well.
2. **A palette value is not "chosen", it is measured.** Any colour that a user
   reads must clear its WCAG 2.2 AA threshold, and the audit that proves it runs
   in CI.

---

## Surfaces and where their colours live

| Surface | Palette source | Used by |
| --- | --- | --- |
| Public research portal | `website/style.css` (`:root` + `@media` blocks) | `website/index.html` |
| Unified workstation | `src/ui/theme.py` (`DARK_QSS` + module constants) | `python -m src.ui.main_window` |
| Doctor / Patient PC | `desktop/workstation_theme.py` (`APP_QSS`, `STATUS_PALETTE`) | `desktop/doctor_app`, `desktop/patient_app` |
| Endo-Twin platform | `apps/main/main_app.py` (inline) | `python apps/main/main_app.py` |
| Developer Control Center | `launcher/main.py` (inline) | `python launcher/main.py` |
| Android Patient / Doctor | `android/*/app/src/main/java/**/ui/theme/EndoTwinTheme.kt` | Kotlin + Compose APKs |
| Alternate premium theme | `src/ui/theme_v83_premium.py` (`DARK` / `LIGHT`) | not wired to an entry point — kept conformant |

---

## The thresholds

| Kind of content | Minimum | WCAG 2.2 |
| --- | --- | --- |
| Body text | 4.5:1 | 1.4.3 |
| Large text (≥24px, or ≥18.66px bold) | 3:1 | 1.4.3 |
| Icons, borders, focus rings, chart strokes that carry meaning | 3:1 | 1.4.11 |
| Focus indicator | 3:1 against the adjacent background | 1.4.11 / 2.4.11 |

The focus indicator is a **two-tone ring**. The invariant is not "both rings
clear 3:1" — no single pair can, because one has to work on light surfaces and
the other on dark ones. The invariant is:

> For any background the control can sit on, `max(contrast(inner, bg),
> contrast(outer, bg)) >= 3`.

`scripts/diagnostics/a11y_contrast_audit.py` tests exactly that, per surface.

---

## Running the audit

```bash
python scripts/diagnostics/a11y_contrast_audit.py        # summary + exit code
python scripts/diagnostics/a11y_contrast_audit.py -v     # per-surface counts
python -m pytest -q tests/test_accessibility_contrast.py # regression suite
```

No third-party packages are required: the tool parses theme *source* (CSS custom
properties, Python constants and dicts, Kotlin `Color(0xFFRRGGBB)` roles), so it
runs in CI before Qt, the Android SDK or a display server exist.

Exit codes: `0` all pairings pass, `1` something is below threshold, `2` a theme
file could not be parsed. A parse failure is treated as a failure — a silently
skipped rule is how a contrast regression gets back in.

Both checks run in `.github/workflows/ui_quality.yml`.

---

## What each surface does

### Website (`website/`)

* Single token layer in `style.css`; light, dark (`prefers-color-scheme`),
  high-contrast (`prefers-contrast: more`) and `forced-colors` variants.
* **Text size control** in the header (`A` / `A+` / `A++`) driving
  `:root[data-text-scale]` (100% / 112.5% / 125%), persisted, announced through a
  polite live region. All type is `rem`-based, so browser zoom still compounds.
* **Skip link** to `<main id="main">`, one `<main>` landmark, labelled `<nav>`.
* Scroll-reveal is *opt-in*: `html.has-reveal` is only added when
  `IntersectionObserver` exists and reduced motion is off, and `script.js`
  force-reveals everything after 2.5 s. A JS failure can never leave the page
  blank.
* Anchors keep native behaviour (focus move, `:target`, history); `script.js`
  only closes the mobile menu.
* Decorative flow icons, arrows and status glyphs carry `aria-hidden="true"`.

### Qt desktop (`src/ui/theme.py`, `desktop/workstation_theme.py`)

* Every selection uses `SEL_BG` / `SEL_TEXT`. The previous light `#E8F3F4`
  selection put `#EAF4FF` text on it — **1.02:1**, invisible.
* `QPushButton:hover` uses `ACCENT_HOVER`. White on the old `ACCENT` was 2.02:1,
  so hovering used to erase the label.
* `QToolTip` is `PANEL_ALT` on `TEXT` (14.5:1); it used to be white on `#EAF4FF`
  (1.11:1).
* Focus uses the `FOCUS` token; `*:focus` rules exist for buttons, inputs,
  tables, lists, trees, tabs, sliders, checkboxes and radios.
* Severity is never colour-only: `VitalCard` renders a state word from
  `STATE_LABELS`, and `GaugeWidget` prints its band ("Low" / "Moderate" /
  "Elevated" / "High") under the percentage.
* Nothing renders below an 11px / 8.5pt floor.

### Android (Compose)

* `outline` is `#6B7785` (4.56:1 on white). It bounds text fields, so the old
  `#D8E0E8` at 1.33:1 was effectively invisible. The old soft tone survives as
  `outlineVariant`, documented as decorative-only.
* `onSurfaceVariant` is `#5A6875` (5.17:1 on `surfaceVariant`).
* Provenance colours (`EndoTwinSemanticColors`) are checked against both
  `surface` and `surfaceVariant`; `demo` moved from `#A66A00` to `#9C6200`
  because amber at 4.05:1 was below AA.
* Compose `sp` units respect the system font scale; body line-heights are set
  explicitly so large-scale text does not collide.

---

## Adding or changing a colour

1. Edit the token, not a one-off literal. If you find yourself typing a hex
   value into a widget file, it belongs in the palette.
2. Run the audit. If it fails, the fix is a different colour — not a different
   threshold.
3. If you add a *pairing* the UI now renders, add it to the audit's matrix so it
   is covered from then on.
4. If you add a surface, add a parser branch and a fixture to
   `tests/test_accessibility_contrast.py`; `test_audit_actually_covers_every_surface`
   fails if a surface silently drops out.

---

## Known limitations

* **Not verified by rendering.** The audit is arithmetic over theme source plus
  static CSS/HTML validation. No browser, Qt display server or Android emulator
  was available, so nothing here is a screenshot-verified claim. Re-check
  visually before release.
* **Screen-reader behaviour is partial.** Accessible names are set on the
  reusable Qt widgets (`VitalCard`, `GaugeWidget`, `card`, `status_badge`) and
  the website carries landmarks, a skip link and `aria-current`, but no NVDA,
  TalkBack or Orca session has been run.
* **Android is not built here.** The Kotlin sources are reviewed and the colour
  roles are checked, but no APK was compiled, so Compose layout under a large
  system font scale is unverified.
* **Colour alone is still used for a few decorative affordances** — chart grid
  lines, card hover elevation. None of them is the sole carrier of information.
* **The alternate premium theme is dead code.** `src/ui/theme_v83_premium.py` is
  not imported by any entry point; it is held to the same thresholds so that
  wiring it up later does not reintroduce failures.
