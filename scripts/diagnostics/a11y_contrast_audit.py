#!/usr/bin/env python3
"""WCAG 2.2 contrast audit for the ENDO-TWIN NEXUS visual system.

Three UI surfaces ship from this repository:

  * the public research portal   -> website/style.css          (CSS custom props)
  * the Qt desktop workstations  -> src/ui/theme.py            (module constants)
  * the Android apps             -> android/*/ui/theme/EndoTwinTheme.kt

Each one declares named colour roles. This script extracts those roles and
checks the foreground/background pairings the interfaces actually rely on,
against WCAG 2.2 AA thresholds:

  body text       4.5:1   (SC 1.4.3)
  large text/UI   3.0:1   (SC 1.4.3, SC 1.4.11)
  focus ring      3.0:1   against every adjacent surface

It is intentionally dependency-free: it parses theme source, so it runs in CI
before any GUI toolkit is installed, and it fails the build rather than letting
a palette drift below threshold.

Usage:
    python scripts/diagnostics/a11y_contrast_audit.py
    python scripts/diagnostics/a11y_contrast_audit.py --verbose

Exit codes:
    0  every pairing meets its threshold
    1  at least one pairing is below threshold
    2  a theme file could not be parsed (treated as a failure too)
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# WCAG 2.2 AA thresholds.
AA_TEXT = 4.5
AA_LARGE = 3.0
AA_UI = 3.0


# --------------------------------------------------------------- colour maths
def _linearise(channel: int) -> float:
    value = channel / 255.0
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_colour: str) -> float:
    """WCAG relative luminance of an #rgb / #rrggbb colour."""
    value = hex_colour.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    if len(value) != 6:
        raise ValueError(f"not a hex colour: {hex_colour!r}")
    red, green, blue = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linearise(red) + 0.7152 * _linearise(green) + 0.0722 * _linearise(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.2 contrast ratio between two opaque colours."""
    a, b = relative_luminance(foreground), relative_luminance(background)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


# ------------------------------------------------------------------- results
@dataclass
class Finding:
    surface: str
    theme: str
    label: str
    foreground: str
    background: str
    ratio: float
    threshold: float

    @property
    def passed(self) -> bool:
        return self.ratio >= self.threshold


def check(
    findings: list[Finding],
    surface: str,
    theme: str,
    label: str,
    foreground: str | None,
    background: str | None,
    threshold: float = AA_TEXT,
) -> None:
    """Record one pairing. Missing tokens are skipped, not silently passed."""
    if not foreground or not background:
        return
    findings.append(
        Finding(
            surface=surface,
            theme=theme,
            label=label,
            foreground=foreground,
            background=background,
            ratio=contrast_ratio(foreground, background),
            threshold=threshold,
        )
    )


# ------------------------------------------------------------------ CSS input
def _css_block(css: str, start: int) -> tuple[str, int]:
    """Return the body of the block whose '{' is at/after `start`, plus its end."""
    open_brace = css.index("{", start)
    depth = 0
    for index in range(open_brace, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[open_brace + 1:index], index + 1
    raise ValueError("unbalanced CSS block")


def _css_vars(body: str) -> dict[str, str]:
    return {
        name: value.lower()
        for name, value in re.findall(r"--([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{3,8})", body)
    }


def parse_website_tokens(css_path: Path) -> dict[str, dict[str, str]]:
    """Extract the token sets for the light, dark and high-contrast themes."""
    css = css_path.read_text(encoding="utf-8")
    # Drop comments so commented-out declarations cannot influence the audit.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    themes: dict[str, dict[str, str]] = {}

    # Base :root — but skip any :root that we will override below.
    for match in re.finditer(r":root[^{]*\{", css):
        selector_start = css.rfind("\n", 0, match.start()) + 1
        pass
    base_match = re.search(r"(?<![-\w]):root\s*(?:\[[^\]]*\])?\s*\{", css)
    if not base_match:
        raise ValueError("no :root token block found")
    base_body, _ = _css_block(css, base_match.start())
    themes["light"] = _css_vars(base_body)

    # prefers-color-scheme / prefers-contrast blocks, in source order.
    order: list[tuple[str, str]] = []
    for match in re.finditer(
        r"@media\s*\(([^)]*)\)\s*(?:and\s*\(([^)]*)\)\s*)?\{", css
    ):
        conditions = " and ".join(c for c in match.groups() if c)
        body, _ = _css_block(css, match.start())
        inner = re.search(r":root\s*(?:\[[^\]]*\])?\s*\{", body)
        if not inner:
            continue
        inner_body, _ = _css_block(body, inner.start())
        order.append((conditions, inner_body))

    for conditions, body in order:
        tokens = _css_vars(body)
        if not tokens:
            continue
        if "prefers-contrast" in conditions:
            theme = (
                "contrast-more-dark"
                if "prefers-color-scheme: dark" in conditions
                else "contrast-more"
            )
        elif "prefers-color-scheme: dark" in conditions:
            theme = "dark"
        else:
            continue
        merged = dict(themes.get(theme.split("-")[0] if theme == "contrast-more" else "light", {}))
        if theme == "dark":
            merged = dict(themes["light"])
        elif theme == "contrast-more":
            merged = dict(themes["light"])
        else:
            # contrast-more-dark layers on the dark theme.
            merged = dict(themes.get("dark", themes["light"]))
        merged.update(tokens)
        themes[theme] = merged

    return themes


def audit_website(findings: list[Finding], verbose: bool) -> None:
    css_path = ROOT / "website" / "style.css"
    if not css_path.exists():
        raise FileNotFoundError(css_path)
    themes = parse_website_tokens(css_path)

    # Pairs the portal actually renders. Token names match style.css.
    text_on_surfaces = [
        ("ink", "body text"),
        ("ink-muted", "secondary text"),
        ("ink-subtle", "chip / meta text"),
    ]
    surfaces = ["page", "surface", "surface-alt"]

    for theme, tokens in themes.items():
        for token, label in text_on_surfaces:
            for surface in surfaces:
                check(
                    findings, "website", theme, f"{label} on {surface}",
                    tokens.get(token), tokens.get(surface), AA_TEXT,
                )
        for surface in surfaces:
            check(
                findings, "website", theme, f"link on {surface}",
                tokens.get("teal"), tokens.get(surface), AA_TEXT,
            )
        for label, fg, bg, threshold in [
            ("hero heading", "hero-ink", "hero", AA_TEXT),
            ("hero subtitle", "hero-muted", "hero", AA_TEXT),
            ("hero accent kicker", "hero-accent", "hero", AA_TEXT),
            ("hero/footer link", "hero-link", "hero", AA_TEXT),
            ("button label", "teal-ink", "teal", AA_TEXT),
            ("button label (hover)", "teal-ink", "teal-strong", AA_TEXT),
            ("nav current link", "teal", "teal-soft", AA_TEXT),
            ("status chip", "badge-ink", "badge-bg", AA_TEXT),
            ("success message", "success", "success-bg", AA_TEXT),
            ("warning message", "warn", "warn-bg", AA_TEXT),
            ("critical message", "danger", "danger-bg", AA_TEXT),
        ]:
            check(findings, "website", theme, label, tokens.get(fg), tokens.get(bg), threshold)

        # Focus uses a two-tone ring. The invariant that actually matters is
        # "for whatever background the ring sits on, at least one of the two
        # halves clears 3:1" (SC 1.4.11 / 2.4.11) — not that each half does.
        ring_backgrounds = [
            ("surface", "card"),
            ("page", "page"),
            ("surface-alt", "alternate section"),
            ("hero", "hero and footer"),
            ("teal", "primary button"),
            ("teal-strong", "primary button (hover)"),
            ("badge-bg", "status chip"),
            ("warn-bg", "demo card"),
            ("danger-bg", "critical callout"),
            ("success-bg", "confirmed callout"),
        ]
        inner = tokens.get("focus-inner")
        outer = tokens.get("focus-outer")
        if inner and outer:
            for background, where in ring_backgrounds:
                value = tokens.get(background)
                if not value:
                    continue
                findings.append(
                    Finding(
                        surface="website",
                        theme=theme,
                        label=f"focus ring pair on {where}",
                        foreground=inner,
                        background=value,
                        ratio=max(contrast_ratio(inner, value), contrast_ratio(outer, value)),
                        threshold=AA_UI,
                    )
                )

    # Non-token literals still present in style.css — audited explicitly.
    literals = [
        ("architecture panel heading", "#ffffff", "#0d2130", AA_TEXT),
        ("architecture panel code", "#dbe6ee", "#0d2130", AA_TEXT),
        ("research disclaimer", "#fdf3dc", "#3a3218", AA_TEXT),
    ]
    for label, fg, bg, threshold in literals:
        check(findings, "website", "light", label, fg, bg, threshold)

    if verbose:
        print(f"  website: {len(themes)} token sets, "
              f"{sum(1 for f in findings if f.surface == 'website')} pairings checked")


# -------------------------------------------------------------- Qt input (.py)
def parse_python_tokens(path: Path) -> dict[str, str]:
    """Extract UPPER_CASE = "#rrggbb" module constants from a Qt theme module."""
    source = path.read_text(encoding="utf-8")
    return {
        name: value.lower()
        for name, value in re.findall(
            r'^([A-Z][A-Z0-9_]*)\s*(?::\s*[^=]+)?=\s*"(#[0-9A-Fa-f]{6})"',
            source,
            flags=re.M,
        )
    }


def audit_qt(findings: list[Finding], verbose: bool) -> None:
    """Audit the dark Qt workstation theme in src/ui/theme.py."""
    theme_path = ROOT / "src" / "ui" / "theme.py"
    if not theme_path.exists():
        raise FileNotFoundError(theme_path)
    tokens = parse_python_tokens(theme_path)
    if not tokens:
        raise ValueError(f"no colour constants parsed from {theme_path}")

    surfaces = ["BG", "PANEL", "PANEL_ALT", "PANEL_HOVER", "TRACK", "PLOT_BG"]
    for surface in surfaces:
        check(findings, "qt-desktop", "dark", f"body text on {surface}",
              tokens.get("TEXT"), tokens.get(surface), AA_TEXT)
        check(findings, "qt-desktop", "dark", f"secondary text on {surface}",
              tokens.get("TEXT_MUTED"), tokens.get(surface), AA_TEXT)
    for surface in ["BG", "PANEL", "PANEL_ALT"]:
        for token in ["ACCENT", "GREEN", "YELLOW", "ORANGE", "RED"]:
            check(findings, "qt-desktop", "dark", f"{token} on {surface}",
                  tokens.get(token), tokens.get(surface), AA_TEXT)
        for token in ["INDIGO", "VIOLET", "PINK"]:
            check(findings, "qt-desktop", "dark", f"{token} on {surface}",
                  tokens.get(token), tokens.get(surface), AA_LARGE)
    for label, fg, bg, threshold in [
        ("primary button label", "#FFFFFF", "ACCENT_DEEP", AA_TEXT),
        ("primary button label (hover)", "#FFFFFF", "ACCENT_HOVER", AA_TEXT),
        ("selected list row", "TEXT", "SEL_BG", AA_TEXT),
        ("selected table row", "TEXT", "SEL_BG", AA_TEXT),
        ("selected tab label", "TEXT", "PANEL_HOVER", AA_TEXT),
        ("tooltip text", "TEXT", "PANEL_ALT", AA_TEXT),
        ("focus ring on panel", "FOCUS", "PANEL", AA_UI),
        ("focus ring on track", "FOCUS", "TRACK", AA_UI),
        ("focus ring on brand fill", "FOCUS", "ACCENT_DEEP", AA_UI),
    ]:
        check(findings, "qt-desktop", "dark", label,
              tokens.get(fg, fg if fg.startswith("#") else None),
              tokens.get(bg, bg if bg.startswith("#") else None), threshold)

    if verbose:
        print(f"  qt desktop: {len(tokens)} tokens parsed")


# --------------------------------------------------------- Compose input (.kt)
def parse_compose_scheme(path: Path) -> dict[str, str]:
    """Extract `role = Color(0xFFRRGGBB)` entries from a Compose color scheme."""
    source = path.read_text(encoding="utf-8")
    scheme: dict[str, str] = {}
    for role, argb in re.findall(
        r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*Color\(0x[fF]{2}([0-9A-Fa-f]{6})\)",
        source,
        flags=re.M,
    ):
        scheme[role] = "#" + argb.lower()
    return scheme


def parse_compose_semantic_colors(path: Path) -> dict[str, str]:
    """Extract `val name = Color(0xFFRRGGBB)` from EndoTwinSemanticColors."""
    source = path.read_text(encoding="utf-8")
    return {
        name: "#" + argb.lower()
        for name, argb in re.findall(
            r"^\s*val\s+([A-Za-z][A-Za-z0-9_]*)\s*=\s*Color\(0x[fF]{2}([0-9A-Fa-f]{6})\)",
            source,
            flags=re.M,
        )
    }


def audit_qt_workstations(findings: list[Finding], verbose: bool) -> None:
    """Audit desktop/workstation_theme.py (Doctor PC + Patient PC shell).

    That module is a plain QSS string rather than a token dict, so the checks
    are anchored on the declarations the accessibility fixes depend on. If one
    of these moves, the audit fails loudly instead of silently skipping.
    """
    path = ROOT / "desktop" / "workstation_theme.py"
    if not path.exists():
        raise FileNotFoundError(path)
    source = path.read_text(encoding="utf-8")
    surface = "qt-workstations"

    def declaration(pattern: str, label: str) -> str:
        match = re.search(pattern, source, flags=re.M)
        if not match:
            # Fail loudly: a silently-skipped rule is how contrast regressions
            # slip back in.
            raise ValueError(f"expected declaration not found: {label}")
        return match.group(1).lower()

    # Focus ring must clear 3:1 against the shells it is drawn over.
    focus = declaration(r'^FOCUS\s*=\s*"(#[0-9A-Fa-f]{6})"', "FOCUS ring constant")
    for shell, name in (("#050d18", "window"), ("#10243a", "card"), ("#0c1d30", "soft panel")):
        check(findings, surface, "dark", f"focus ring on {name}", focus, shell, AA_UI)

    # Primary button label sits on both gradient stops, rest and hover.
    stops = re.findall(
        r"QPushButton#primary[^{]*\{[^}]*?stop:0\s*(#[0-9A-Fa-f]{6})[^}]*?stop:1\s*(#[0-9A-Fa-f]{6})",
        source, flags=re.S)
    hover_stops = re.findall(
        r"QPushButton#primary:hover\s*\{[^}]*?stop:0\s*(#[0-9A-Fa-f]{6})[^}]*?stop:1\s*(#[0-9A-Fa-f]{6})",
        source, flags=re.S)
    for index, pair in enumerate(stops):
        for stop in pair:
            check(findings, surface, "dark",
                  f"primary button label on gradient stop {stop}",
                  "#FFFFFF", stop, AA_TEXT)
    for pair in hover_stops:
        for stop in pair:
            check(findings, surface, "dark",
                  f"primary button label on hover stop {stop}",
                  "#FFFFFF", stop, AA_TEXT)
    if not stops:
        raise ValueError("expected declaration not found: primary button gradient")

    # Selected rows and inputs must keep readable text.
    for rule, label in (("QTableWidget::item:selected", "selected table row"),
                        ("QListWidget::item:selected", "selected list row")):
        match = re.search(
            rule + r"\s*\{([^}]*)\}", source)
        if not match:
            raise ValueError(f"expected declaration not found: {rule}")
        body = match.group(1)
        background = re.search(r"background:\s*(#[0-9A-Fa-f]{6})", body)
        check(findings, surface, "dark", f"{label} text",
              "#FFFFFF", background.group(1) if background else None, AA_TEXT)

    # Tooltip and progress readouts.
    tooltip = re.search(r"QToolTip\s*\{([^}]*)\}", source)
    if tooltip:
        body = tooltip.group(1)
        fg = re.search(r"color:\s*(#[0-9A-Fa-f]{6})", body)
        bg = re.search(r"background:\s*(#[0-9A-Fa-f]{6})", body)
        check(findings, surface, "dark", "tooltip text",
              fg.group(1) if fg else None, bg.group(1) if bg else None, AA_TEXT)

    # Provenance badges: every foreground against its own tinted background.
    palette_block = re.search(r"STATUS_PALETTE\s*=\s*\{(.*?)\n\}", source, flags=re.S)
    if not palette_block:
        raise ValueError("expected declaration not found: STATUS_PALETTE")
    entries = re.findall(
        r'"([a-z_]+)":\s*\("(#[0-9A-Fa-f]{6})",\s*"(#[0-9A-Fa-f]{6})"',
        palette_block.group(1))
    if not entries:
        raise ValueError("expected declaration not found: STATUS_PALETTE entries")
    for kind, background, foreground in entries:
        check(findings, surface, "dark", f"{kind} badge label",
              foreground, background, AA_TEXT)

    if verbose:
        badge_kinds = len(re.findall(r'"([a-z_]+)":', palette_block.group(1)))
        print(f"  qt workstations: {len(stops) + len(hover_stops)} gradients, "
              f"{badge_kinds} badge kinds parsed")


def audit_qt_premium(findings: list[Finding], verbose: bool) -> None:
    """Audit the alternate premium palettes in src/ui/theme_v83_premium.py.

    Not currently imported by any entry point, but it ships in the repository
    and defines both a dark and a light palette, so both are held to the same
    contract as the live theme.
    """
    path = ROOT / "src" / "ui" / "theme_v83_premium.py"
    if not path.exists():
        raise FileNotFoundError(path)
    source = path.read_text(encoding="utf-8")

    parsed = 0
    for name in ("DARK", "LIGHT"):
        block = re.search(name + r"\s*=\s*\{(.*?)\n\}", source, flags=re.S)
        if not block:
            raise ValueError(f"expected palette dict not found: {name}")
        palette = {
            key: value.lower()
            for key, value in re.findall(
                r'"([a-z_0-9]+)":\s*"(#[0-9A-Fa-f]{6})"', block.group(1)
            )
        }
        if not palette:
            raise ValueError(f"no colours parsed from palette: {name}")
        parsed += len(palette)
        theme = name.lower()
        text_roles = [r for r in ("text", "text_muted", "text_secondary") if r in palette]
        surface_roles = [
            r for r in ("bg", "panel", "panel_alt", "panel_hover") if r in palette
        ]
        for role in text_roles:
            for surface in surface_roles:
                check(findings, "qt-premium", theme, f"{role} on {surface}",
                      palette[role], palette[surface], AA_TEXT)
        if "accent" in palette and "panel" in palette:
            check(findings, "qt-premium", theme, "accent on panel",
                  palette["accent"], palette["panel"], AA_LARGE)

    if verbose:
        print(f"  qt premium: {parsed} colours across 2 palettes")


def audit_compose(findings: list[Finding], verbose: bool) -> None:
    """Audit both Android colour schemes against their own surfaces."""
    targets = [
        ("patient", ROOT / "android" / "patient" / "app" / "src" / "main"
         / "java" / "org" / "chronopcos" / "patient" / "ui" / "theme" / "EndoTwinTheme.kt"),
        ("doctor", ROOT / "android" / "doctor" / "app" / "src" / "main"
         / "java" / "org" / "chronopcos" / "doctor" / "ui" / "theme" / "EndoTwinTheme.kt"),
    ]
    for app, path in targets:
        if not path.exists():
            raise FileNotFoundError(path)
        scheme = parse_compose_scheme(path)
        if not scheme:
            raise ValueError(f"no Compose colour roles parsed from {path}")

        # Material 3 role pairs: content colour against its own container.
        pairs = [
            ("primary", "onPrimary", AA_TEXT),
            ("primaryContainer", "onPrimaryContainer", AA_TEXT),
            ("secondary", "onSecondary", AA_TEXT),
            ("secondaryContainer", "onSecondaryContainer", AA_TEXT),
            ("tertiary", "onTertiary", AA_TEXT),
            ("tertiaryContainer", "onTertiaryContainer", AA_TEXT),
            ("error", "onError", AA_TEXT),
            ("background", "onBackground", AA_TEXT),
            ("surface", "onSurface", AA_TEXT),
            ("surfaceVariant", "onSurfaceVariant", AA_TEXT),
        ]
        for container, content, threshold in pairs:
            check(findings, f"android-{app}", "material3", f"{content} on {container}",
                  scheme.get(content), scheme.get(container), threshold)

        # Outline must be perceivable against the surface it bounds (SC 1.4.11).
        check(findings, f"android-{app}", "material3", "outline on surface",
              scheme.get("outline"), scheme.get("surface"), AA_UI)
        check(findings, f"android-{app}", "material3", "primary on surface",
              scheme.get("primary"), scheme.get("surface"), AA_TEXT)
        check(findings, f"android-{app}", "material3", "error on surface",
              scheme.get("error"), scheme.get("surface"), AA_TEXT)

        # Provenance colours are rendered as text on the light surfaces.
        semantics = parse_compose_semantic_colors(path)
        for name, value in semantics.items():
            check(findings, f"android-{app}", "provenance", f"{name} label on surface",
                  value, scheme.get("surface"), AA_TEXT)
            check(findings, f"android-{app}", "provenance", f"{name} label on surfaceVariant",
                  value, scheme.get("surfaceVariant"), AA_TEXT)

        if verbose:
            print(f"  android {app}: {len(scheme)} colour roles, "
                  f"{len(semantics)} provenance colours parsed")


# ---------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="print per-surface token counts")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    problems: list[str] = []

    print("ENDO-TWIN NEXUS accessibility contrast audit (WCAG 2.2 AA)")
    print("=" * 72)

    for label, runner in (
        ("website/style.css", audit_website),
        ("src/ui/theme.py", audit_qt),
        ("desktop/workstation_theme.py", audit_qt_workstations),
        ("src/ui/theme_v83_premium.py", audit_qt_premium),
        ("android/*/EndoTwinTheme.kt", audit_compose),
    ):
        try:
            runner(findings, args.verbose)
        except (FileNotFoundError, ValueError) as error:
            problems.append(f"{label}: {error}")

    for surface in sorted({f.surface for f in findings}):
        rows = [f for f in findings if f.surface == surface]
        failures = [f for f in rows if not f.passed]
        status = "PASS" if not failures else "FAIL"
        print(f"\n[{status}] {surface}: {len(rows) - len(failures)}/{len(rows)} pairings meet AA")
        for failure in failures:
            print(
                f"    {failure.ratio:5.2f}:1  (need {failure.threshold}:1)  "
                f"{failure.theme} :: {failure.label}  "
                f"{failure.foreground} on {failure.background}"
            )

    total = len(findings)
    failures = [f for f in findings if not f.passed]
    print("\n" + "=" * 72)
    print(f"checked {total} colour pairings, {len(failures)} below threshold, "
          f"{len(problems)} file problem(s)")
    for problem in problems:
        print(f"  ! {problem}")

    if failures or problems:
        worst = min((f.ratio for f in findings), default=0.0)
        print(f"lowest ratio observed: {worst:.2f}:1")
        return 1

    print("all pairings meet WCAG 2.2 AA — nothing relies on colour alone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
