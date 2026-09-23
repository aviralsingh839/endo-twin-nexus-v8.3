"""Wear-site contract: the pod is worn on the wrist or the shoulder.

These tests protect three things:

1. the site is validated and can be overridden per session;
2. every reported channel has an explicit meaning *and* an explicit limit for both
   sites, so the UI never shows a site-less number;
3. the site stays host-side - the `$CP3` frame is unchanged, so old firmware and
   old recordings keep working.
"""
from pathlib import Path

import pytest

from src.core import wear_site

REPO = Path(__file__).resolve().parents[1]


def test_default_site_is_valid_and_labelled():
    assert wear_site.normalize_site(None) == wear_site.DEFAULT_WEAR_SITE
    assert "wrist" in wear_site.site_label("wrist").lower()
    assert "shoulder" in wear_site.site_label("shoulder").lower()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("wrist", "wrist"),
        ("WRIST", "wrist"),
        ("forearm", "wrist"),
        ("shoulder", "shoulder"),
        ("upper-arm", "shoulder"),
        ("upper_arm", "shoulder"),
        ("deltoid", "shoulder"),
    ],
)
def test_site_aliases_resolve(raw, expected):
    assert wear_site.normalize_site(raw) == expected


def test_unknown_site_is_rejected():
    with pytest.raises(ValueError):
        wear_site.normalize_site("ankle")


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv(wear_site.ENV_VAR, "shoulder")
    assert wear_site.active_site() == "shoulder"
    assert wear_site.site_tag() == "SITE=shoulder"
    monkeypatch.setenv(wear_site.ENV_VAR, "wrist")
    assert wear_site.active_site() == "wrist"


def test_env_override_rejects_nonsense(monkeypatch):
    monkeypatch.setenv(wear_site.ENV_VAR, "elbow")
    with pytest.raises(ValueError):
        wear_site.active_site()


def test_every_channel_is_documented_for_both_sites():
    for site in wear_site.WEAR_SITES:
        notes = wear_site.MEASUREMENT_NOTES[site]
        assert set(notes) == set(wear_site.CHANNELS), f"{site} is missing channels"
        for channel, note in notes.items():
            assert note["meaning"].strip(), f"{site}/{channel} has no meaning"
            assert note["limits"], f"{site}/{channel} has no stated limit"
            for limit in note["limits"]:
                assert limit.strip()


def test_sites_are_not_interchangeable():
    """The guide must say out loud that the two sites cannot be compared."""
    assert "not comparable" in wear_site.CROSS_SITE_RULE.lower()
    for site in wear_site.WEAR_SITES:
        assert wear_site.CROSS_SITE_RULE in wear_site.guide_text(site)
        assert wear_site.caption(site).startswith("WORN:")
    # the channels whose meaning genuinely differs carry different text per site
    for channel in ("motion_activity", "skin_temp_c", "ambient_light", "room_environment"):
        wrist = wear_site.channel_note(channel, "wrist")["meaning"]
        shoulder = wear_site.channel_note(channel, "shoulder")["meaning"]
        assert wrist != shoulder, f"{channel} reads identically on both sites"


def test_mounting_guidance_exists_for_both_sites():
    for site in wear_site.WEAR_SITES:
        mount = wear_site.mounting(site)
        assert mount["strap"].strip()
        assert len(mount["pod_orientation"]) >= 3
        assert mount["watch_out_for"]


def test_unknown_channel_is_rejected():
    with pytest.raises(KeyError):
        wear_site.channel_note("gsr_raw", "wrist")


def test_wire_format_is_unchanged_by_the_site():
    """The site must never leak into $CP3: 24 parts, no site field."""
    parser_source = (REPO / "src/serial_io/packet_parser.py").read_text(encoding="utf-8")
    assert "wear_site" not in parser_source
    assert "CP3" in parser_source
    cp3_line = next(
        line for line in parser_source.split("\n") if line.startswith("$CP3,")
    )
    assert len(cp3_line.strip().rstrip(",").split(",")) == 24, cp3_line


def test_ui_and_reports_surface_the_site():
    """Numbers are shown with their site, not bare."""
    for relative, marker in (
        ("desktop/workstation_runtime.py", '"wear_site":active_site()'),
        ("desktop/workstation_runtime.py", "site_tag()"),
        ("desktop/doctor_app/main_enhanced.py", "site_caption()"),
        ("desktop/patient_app/main.py", "wear_site"),
        ("reports/report_generator.py", "wear_site.site_label()"),
        ("src/utils/public_study.py", "wear_site"),
        ("desktop/prototype_lab.py", "wear site"),
    ):
        text = (REPO / relative).read_text(encoding="utf-8")
        assert marker in text, f"{relative} does not surface the wear site ({marker})"


def test_cli_prints_a_guide_for_both_sites(capsys):
    assert wear_site.main(["--both"]) == 0
    out = capsys.readouterr().out
    assert "WEAR SITE: Wrist" in out
    assert "WEAR SITE: Shoulder" in out
    assert "not comparable" in out.lower()
    assert wear_site.main(["ankle"]) == 2


def test_docs_exist_and_cover_both_sites():
    doc = (REPO / "docs/WEAR_SITES.md").read_text(encoding="utf-8")
    for needle in ("wrist", "shoulder", "never compared", "baseline belongs to a site", "probe", "strap"):
        assert needle.lower() in doc.lower(), f"docs/WEAR_SITES.md lacks {needle!r}"
    manual = (REPO / "docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md").read_text(encoding="utf-8")
    assert "WEAR_SITES.md" in manual
    assert "shoulder" in manual.lower()
    readme = (REPO / "docs/README.md").read_text(encoding="utf-8")
    assert "WEAR_SITES.md" in readme


def test_config_declares_the_default_site():
    from src import config

    assert config.WEAR_SITE in wear_site.WEAR_SITES


def test_cardboard_build_guide_is_complete():
    """The physical build has one entry point: the cardboard guide."""
    guide = (REPO / "docs/CARDBOARD_POD_BUILD.md").read_text(encoding="utf-8")
    for needle in (
        "no battery",              # v1 scope
        "Contact test",            # the verification the user must run
        "upper arm",               # both sites covered
        "gasket",                  # the optical seal
        "USB",                     # power path
        "Strap tension",
    ):
        assert needle.lower() in guide.lower(), f"build guide lacks {needle!r}"
    # every figure it references exists
    import re

    for ref in re.findall(r"\]\(images/wearable/([^)]+)\)", guide):
        assert (REPO / "docs/images/wearable" / ref).is_file(), f"missing figure {ref}"
    # the reference manual points at it and no longer claims a battery in v1
    manual = (REPO / "docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md").read_text(encoding="utf-8")
    assert "CARDBOARD_POD_BUILD.md" in manual
    assert "USB power and data (no battery in v1)" in manual
    # docs index exposes it
    assert "CARDBOARD_POD_BUILD.md" in (REPO / "docs/README.md").read_text(encoding="utf-8")


def test_upper_arm_ppg_limits_are_stated_with_evidence():
    """The guide must not claim the upper arm works unconditionally."""
    guide = (REPO / "docs/CARDBOARD_POD_BUILD.md").read_text(encoding="utf-8")
    assert "wrist" in guide.lower()
    assert "saturating" in guide.lower()
    assert "0x24" in guide            # the gain value the firmware actually uses
    assert "0x3F" in guide            # the alternative it tells you to try
    assert "(https://" in guide       # cited study, not a bare assertion
    firmware = (REPO / "hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino").read_text(encoding="utf-8")
    assert "setPulseAmplitudeIR(0x24)" in firmware, "guide quotes a gain the firmware no longer uses"
