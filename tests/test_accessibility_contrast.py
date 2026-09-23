"""Accessibility regression tests for the ENDO-TWIN NEXUS visual system.

These are deliberately dependency-free: they read the theme *source* rather
than importing the GUI toolkits, so they run in CI before PySide6, the Android
SDK or a display server exist.

What is protected here:
  * WCAG 2.2 AA contrast for every colour pairing the three surfaces render
    (see scripts/diagnostics/a11y_contrast_audit.py for the full matrix).
  * The presence of the accessibility affordances that are easy to delete
    during a redesign: on-page text-size control, skip link, visible focus
    rings, reduced-motion handling, and touch-target floors.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "diagnostics"))

import a11y_contrast_audit as audit  # noqa: E402


# --------------------------------------------------------------------------
# Contrast
# --------------------------------------------------------------------------
def _run_audit() -> list[audit.Finding]:
    findings: list[audit.Finding] = []
    audit.audit_website(findings, verbose=False)
    audit.audit_qt(findings, verbose=False)
    audit.audit_qt_workstations(findings, verbose=False)
    audit.audit_qt_premium(findings, verbose=False)
    audit.audit_compose(findings, verbose=False)
    return findings


@pytest.fixture(scope="module")
def findings() -> list[audit.Finding]:
    return _run_audit()


def test_audit_actually_covers_every_surface(findings):
    """A silent parse failure would otherwise make every check below vacuous."""
    surfaces = {finding.surface for finding in findings}
    assert surfaces == {
        "website", "qt-desktop", "qt-workstations", "qt-premium",
        "android-patient", "android-doctor",
    }, f"audit lost a surface: {sorted(surfaces)}"
    assert len(findings) > 250, f"expected a broad matrix, checked {len(findings)}"


def test_every_colour_pairing_meets_wcag_aa(findings):
    failures = [
        f"{f.surface}/{f.theme}: {f.label} {f.foreground} on {f.background} "
        f"= {f.ratio:.2f}:1 (needs {f.threshold}:1)"
        for f in findings if not f.passed
    ]
    assert not failures, "contrast below WCAG 2.2 AA:\n  " + "\n  ".join(failures)


def test_exit_code_is_zero_when_all_pairings_pass():
    assert audit.main([]) == 0


# --------------------------------------------------------------------------
# Contrast maths — guard the measurement itself
# --------------------------------------------------------------------------
@pytest.mark.parametrize("foreground,background,expected", [
    ("#000000", "#ffffff", 21.0),
    ("#ffffff", "#ffffff", 1.0),
    ("#0b6670", "#ffffff", 6.67),
])
def test_contrast_ratio_reference_values(foreground, background, expected):
    assert audit.contrast_ratio(foreground, background) == pytest.approx(expected, abs=0.01)


def test_contrast_ratio_is_symmetric():
    a = audit.contrast_ratio("#123456", "#abcdef")
    b = audit.contrast_ratio("#abcdef", "#123456")
    assert a == pytest.approx(b)


# --------------------------------------------------------------------------
# Website affordances
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def website_css() -> str:
    return (PROJECT_ROOT / "website" / "style.css").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def website_html() -> str:
    return (PROJECT_ROOT / "website" / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def website_js() -> str:
    return (PROJECT_ROOT / "website" / "script.js").read_text(encoding="utf-8")


def test_website_has_a_skip_link(website_html, website_css):
    assert 'class="skip-link"' in website_html
    assert ".skip-link:focus" in website_css


def test_website_has_one_main_landmark(website_html):
    assert website_html.count("<main") == 1
    assert website_html.count("</main>") == 1


def test_website_offers_on_page_text_scaling(website_html, website_css, website_js):
    """WCAG 1.4.4: users must be able to resize text without loss of content."""
    assert 'data-text-scale="large"' in website_html
    assert 'data-text-scale="xlarge"' in website_html
    assert 'aria-pressed' in website_html
    assert 'data-text-scale="large"' in website_css
    assert "data-text-scale" in website_js


def test_website_declares_focus_visible_styles(website_css):
    assert ":focus-visible" in website_css
    # The ring must define a colour rather than relying on the UA default.
    assert "--focus-inner" in website_css and "--focus-outer" in website_css


def test_website_respects_reduced_motion(website_css, website_js):
    assert "prefers-reduced-motion: reduce" in website_css
    assert "prefers-reduced-motion" in website_js


def test_website_supports_forced_colors_and_high_contrast(website_css):
    assert "forced-colors: active" in website_css
    assert "prefers-contrast: more" in website_css


def test_website_reflow_does_not_force_horizontal_scroll(website_css):
    """WCAG 1.4.10: no fixed min-width that forces sideways scrolling at 320px."""
    assert "min-width: 560px" not in website_css
    assert "overflow-wrap" in website_css


def test_website_type_is_relative_not_pinned(website_css):
    """Root size stays overridable, so browser zoom and the control both work."""
    assert "--measure:" in website_css
    # The base root size stays a plain percentage so browser zoom, the OS font
    # setting and the on-page control all compound instead of fighting.
    assert re.search(r":root\s*\{\s*font-size:\s*100%", website_css)
    assert ':root[data-text-scale="large"]' in website_css
    assert ':root[data-text-scale="xlarge"]' in website_css


def test_website_scripts_load_without_escaping(website_html):
    """A double-escaped script src silently kills the whole progressive layer."""
    assert '<script src="script.js">' in website_html
    assert '\\"script.js\\"' not in website_html


def test_website_state_is_never_colour_only(website_html, website_css, website_js):
    """Status must carry a glyph or word alongside the tint."""
    assert 'ul.positive li::before' in website_css
    assert 'ul.negative li::before' in website_css
    assert "DEMO DATA" in website_css          # demo provider cards
    assert 'aria-current' in website_js        # current nav section


def test_website_decorative_glyphs_are_hidden_from_screen_readers(website_html):
    assert website_html.count('aria-hidden="true"') > 20


# --------------------------------------------------------------------------
# Qt desktop affordances
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def qt_theme_source() -> str:
    return (PROJECT_ROOT / "src" / "ui" / "theme.py").read_text(encoding="utf-8")


def test_qt_focus_rings_use_the_focus_token(qt_theme_source):
    assert 'FOCUS = "#FFFFFF"' in qt_theme_source
    assert "{FOCUS}" in qt_theme_source


def test_qt_selection_colours_are_not_a_light_fill(qt_theme_source):
    """The old #E8F3F4 selection put near-white text on a near-white row."""
    assert "SEL_BG" in qt_theme_source
    assert "{SEL_BG}" in qt_theme_source
    # Any remaining literal light fill on a selection would be a regression.
    assert "selection-background-color: #E8F3F4" not in qt_theme_source


def test_qt_qss_has_no_escaped_newline_bug(qt_theme_source):
    """A literal backslash-n swallows the declaration that follows it."""
    qss = re.search(r'DARK_QSS = f"""(.*?)"""', qt_theme_source, flags=re.S)
    assert qss, "DARK_QSS block not found"
    offenders = [line for line in qss.group(1).splitlines() if "\\n" in line]
    assert not offenders, f"escaped newline inside the stylesheet: {offenders}"


def test_qt_tooltip_is_not_light_on_light(qt_theme_source):
    tooltip = re.search(r"QToolTip \{\{(.*?)\}\}", qt_theme_source, flags=re.S)
    assert tooltip, "QToolTip rule not found"
    body = tooltip.group(1)
    assert "{PANEL_ALT}" in body and "{TEXT}" in body
    assert "color: #FFFFFF" not in body


def test_qt_vital_card_state_carries_a_word():
    """Severity must survive greyscale, so the widget exports its state word."""
    source = (PROJECT_ROOT / "src" / "ui" / "vital_cards.py").read_text(encoding="utf-8")
    assert "STATE_LABELS" in source
    assert '"red": "High"' in source
    assert "state_label" in source


def test_qt_gauge_reports_its_band_in_words():
    """The dial colour reinforced the band; it must not be the only channel."""
    source = (PROJECT_ROOT / "src" / "ui" / "gauges.py").read_text(encoding="utf-8")
    assert "def band_label" in source
    for word in ("Low", "Moderate", "Elevated", "High"):
        assert f'"{word}"' in source


def test_qt_workstation_badges_are_contrast_checked():
    source = (PROJECT_ROOT / "desktop" / "workstation_theme.py").read_text(encoding="utf-8")
    assert "STATUS_PALETTE" in source
    # Text must not drop below the 11px legibility floor.
    sizes = [int(size) for size in re.findall(r"font-size:(\d+)px", source)]
    assert sizes, "no pixel font sizes found in the workstation sheet"
    assert min(sizes) >= 11, f"font below the 11px floor: {min(sizes)}px"


@pytest.mark.parametrize("relative_path", [
    "launcher/main.py",
    "apps/main/main_app.py",
    "desktop/doctor_app/main_enhanced.py",
    "desktop/patient_app/main.py",
])
def test_desktop_surfaces_keep_an_11px_type_floor(relative_path):
    """These sheets used 9px/10px footnotes — about 6pt on a 96-dpi screen."""
    source = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    sizes = [float(size) for size in re.findall(r"font-size:\s*([0-9.]+)px", source)]
    assert sizes, f"no pixel font sizes found in {relative_path}"
    assert min(sizes) >= 11, f"{relative_path} drops to {min(sizes)}px"


# --------------------------------------------------------------------------
# Android affordances
# --------------------------------------------------------------------------
@pytest.mark.parametrize("app", ["patient", "doctor"])
def test_android_outline_is_perceivable(app):
    """Outlines bound text fields, so SC 1.4.11 requires 3:1 against surface."""
    path = (PROJECT_ROOT / "android" / app / "app" / "src" / "main" / "java"
            / "org" / "chronopcos" / app / "ui" / "theme" / "EndoTwinTheme.kt")
    scheme = audit.parse_compose_scheme(path)
    assert scheme, f"no colour roles parsed from {path}"
    ratio = audit.contrast_ratio(scheme["outline"], scheme["surface"])
    assert ratio >= 3.0, f"{app} outline is {ratio:.2f}:1 against surface"


@pytest.mark.parametrize("app", ["patient", "doctor"])
def test_android_decorative_divider_is_labeled_as_such(app):
    """The soft tone must stay out of the interactive-role slot."""
    path = (PROJECT_ROOT / "android" / app / "app" / "src" / "main" / "java"
            / "org" / "chronopcos" / app / "ui" / "theme" / "EndoTwinTheme.kt")
    source = path.read_text(encoding="utf-8")
    assert "outlineVariant" in source
    assert "Never use it to" in source or "decorative" in source.lower()
