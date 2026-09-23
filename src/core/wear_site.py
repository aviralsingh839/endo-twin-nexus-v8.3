"""Where the wearable sits, and what that does to each measurement.

The pod can be worn on the **wrist** (forearm) or the **shoulder** (upper arm /
deltoid). Placement is a host-side concept: it never enters the `$CP3` frame, so
the wire contract is unchanged. The site is recorded with a session and shown
next to the numbers, because the same channel does not mean the same thing on
the two sites.

The rule that matters most: **a personal baseline belongs to a site.** Switching
site changes the limb, the perfusion and the clothing around the pod, so it
looks like a physiological change in the trend when it is a configuration
change. Record the site, and start a new baseline when it changes.

This module is deliberately plain data plus tiny helpers: no inference, no
thresholds that pretend to be clinical reference values.

Run it directly for the printable guide:

    python -m src.core.wear_site            # active site
    python -m src.core.wear_site wrist      # a specific site
    python -m src.core.wear_site --both
"""
from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Tuple

WEAR_SITES: Tuple[str, ...] = ("wrist", "shoulder")
DEFAULT_WEAR_SITE = "wrist"
ENV_VAR = "ENDO_TWIN_WEAR_SITE"

SITE_LABELS: Dict[str, str] = {
    "wrist": "Wrist (forearm, pod on the inner side)",
    "shoulder": "Shoulder (upper arm / deltoid)",
}

#: Short tag written into provenance strings, e.g. "MEASURED • SITE=wrist".
SITE_TAG_TEMPLATE = "SITE={site}"

CROSS_SITE_RULE = (
    "Wrist and shoulder sessions are not comparable: keep one site per session, "
    "record it, and start a new personal baseline when the site changes."
)

#: How to physically mount the pod on each site. Engineering guidance, not
#: a validated fitting procedure.
SITE_MOUNTING: Dict[str, Dict[str, object]] = {
    "wrist": {
        "strap": "20-25 mm strap around the forearm; snug enough that the pod cannot rock, "
                 "loose enough to leave no mark after 30 minutes",
        "pod_orientation": (
            "MAX30102 window flat against the inner (volar) wrist, proximal to the wrist "
            "crease and clear of the bony ulnar head",
            "BH1750 facing outwards so it can see ambient light",
            "BME280 vent facing away from skin",
            "DS18B20 probe flat on the inner forearm beside the pod, 15+ mm from the "
            "PPG window",
        ),
        "watch_out_for": (
            "strap creeping loose during the day (bad contact shows as a quality drop)",
            "sleeves covering the light sensor",
            "the probe pressing on the PPG site or the strap seam",
        ),
    },
    "shoulder": {
        "strap": "armband over the deltoid or upper arm; it must not slide when the arm "
                 "swings, and must not be tightened over the shoulder joint itself",
        "pod_orientation": (
            "MAX30102 window flat against skin on the inner upper arm - not through a "
            "sleeve, and not over the outer deltoid where contact is poor",
            "BH1750 facing outwards if the sleeve allows it; expect darkness under clothing",
            "BME280 vent away from skin (under clothing it measures microclimate, not room air)",
            "DS18B20 probe flat on the inner upper arm, 20+ mm from the pod body and clear "
            "of the armpit crease",
        ),
        "watch_out_for": (
            "clothing between sensor and skin (PPG needs optical contact, not fabric)",
            "the pod pressed by a bag strap or seat belt",
            "probe reading trapped warm air instead of skin if it lifts at the edge",
        ),
    },
}

#: What each reported channel means on each site, and where it stops being
#: trustworthy. Keys are host-side channel names, not wire fields.
MEASUREMENT_NOTES: Dict[str, Dict[str, Dict[str, object]]] = {
    "wrist": {
        "hr_bpm": {
            "meaning": "Heart rate from the MAX30102 PPG on the wrist, quality-gated before it is used.",
            "limits": (
                "motion from the hand, wrist or a loose strap contaminates beats",
                "ambient light leaking under the strap shows up as a quality drop",
            ),
        },
        "hrv": {
            "meaning": "RMSSD/SDNN derived from the same wrist PPG intervals - a derived value, not an ECG measurement.",
            "limits": (
                "PPG-derived HRV is less accurate than ECG-derived HRV",
                "arm movement during the window makes the value unusable rather than merely noisy",
            ),
        },
        "spo2_pct": {
            "meaning": "Ratio-derived oxygen saturation indicator from the wrist PPG, shown only above a stricter quality gate.",
            "limits": ("not a clinical pulse oximeter reading",),
        },
        "skin_temp_c": {
            "meaning": "DS18B20 probe in skin contact on the forearm; a local skin temperature trend.",
            "limits": (
                "the wrist is a distal site: it follows the environment more than a proximal site does",
                "not core body temperature",
                "a lifted probe reports the air beside the arm - check status bit 3",
            ),
        },
        "motion_activity": {
            "meaning": "MPU6050 motion on the forearm, classified into an activity level.",
            "limits": (
                "the wrist amplifies arm swing, so the same walk looks larger than it does from the shoulder",
                "desk work and phone use register as movement",
                "not whole-body calorimetry or step counting",
            ),
        },
        "ambient_light": {
            "meaning": "BH1750 illuminance in lux, used as day/night and light-exposure context.",
            "limits": ("a sleeve over the pod turns this into a clothing sensor",),
        },
        "room_environment": {
            "meaning": "BME280 temperature, humidity and pressure behind the pod's vents.",
            "limits": (
                "with the pod against the arm this is close to ambient air, not a calibrated room sensor",
                "body heat biases the temperature upward",
            ),
        },
    },
    "shoulder": {
        "hr_bpm": {
            "meaning": "Heart rate from the MAX30102 PPG on the upper arm, quality-gated before it is used.",
            "limits": (
                "the upper arm is not the validated site for PPG: expect lower signal amplitude and rely on the quality gate",
                "fabric between sensor and skin stops the measurement entirely - mount on skin",
                "arm and torso movement couple into the reading",
            ),
        },
        "hrv": {
            "meaning": "RMSSD/SDNN derived from upper-arm PPG intervals - a derived value on a non-standard site.",
            "limits": (
                "treat upper-arm HRV as exploratory; the quality gate matters more here than on the wrist",
                "not comparable with wrist sessions",
            ),
        },
        "spo2_pct": {
            "meaning": "Ratio-derived oxygen saturation indicator from the upper-arm PPG, shown only above a stricter quality gate.",
            "limits": ("non-standard site for this ratio; context only, never a clinical reading",),
        },
        "skin_temp_c": {
            "meaning": "DS18B20 probe in skin contact on the upper arm; a local skin temperature trend.",
            "limits": (
                "the upper arm is clothed far more often, so the probe measures skin plus trapped warm air",
                "absolute values sit differently from the wrist - compare within a site, not across sites",
                "not core body temperature",
            ),
        },
        "motion_activity": {
            "meaning": "MPU6050 motion on the upper arm, classified into an activity level.",
            "limits": (
                "the shoulder moves with the torso, so arm-only movement looks smaller than it does from the wrist",
                "bag straps, seat belts and leaning on the pod add motion that is not activity",
                "not whole-body calorimetry",
            ),
        },
        "ambient_light": {
            "meaning": "BH1750 illuminance in lux, only usable when the sleeve leaves the sensor exposed.",
            "limits": ("under clothing this reads darkness regardless of the actual light level, so it is context at best",),
        },
        "room_environment": {
            "meaning": "BME280 temperature/humidity/pressure behind the pod vents on the upper arm - "
                       "normally an under-garment microclimate, not room air.",
            "limits": (
                "under clothing this is warm and humid compared with the room: microclimate, not environment",
                "do not read it as room temperature or humidity, and do not compare it with a wrist session",
            ),
        },
    },
}

CHANNELS: Tuple[str, ...] = tuple(MEASUREMENT_NOTES[DEFAULT_WEAR_SITE].keys())


def normalize_site(value: Optional[str]) -> str:
    """Return a valid site name, raising ValueError for anything else."""
    if value is None or str(value).strip() == "":
        return DEFAULT_WEAR_SITE
    candidate = str(value).strip().lower().replace("-", "_")
    aliases = {
        "wrist": "wrist",
        "forearm": "wrist",
        "shoulder": "shoulder",
        "upper_arm": "shoulder",
        "upperarm": "shoulder",
        "arm": "shoulder",
        "deltoid": "shoulder",
    }
    if candidate not in aliases:
        raise ValueError(
            f"unknown wear site {value!r}; choose one of {', '.join(WEAR_SITES)} "
            f"(or set {ENV_VAR})"
        )
    return aliases[candidate]


def active_site() -> str:
    """Site for this session: environment override, then `src.config.WEAR_SITE`."""
    override = os.environ.get(ENV_VAR)
    if override:
        return normalize_site(override)
    try:
        from src import config

        return normalize_site(getattr(config, "WEAR_SITE", DEFAULT_WEAR_SITE))
    except Exception:
        return DEFAULT_WEAR_SITE


def site_label(site: Optional[str] = None) -> str:
    return SITE_LABELS[normalize_site(site if site is not None else active_site())]


def site_tag(site: Optional[str] = None) -> str:
    """Short provenance tag such as ``SITE=shoulder``."""
    return SITE_TAG_TEMPLATE.format(site=normalize_site(site if site is not None else active_site()))


def channel_note(channel: str, site: Optional[str] = None) -> Dict[str, object]:
    resolved = normalize_site(site if site is not None else active_site())
    try:
        return MEASUREMENT_NOTES[resolved][channel]
    except KeyError as exc:
        raise KeyError(f"unknown channel {channel!r} for site {resolved!r}") from exc


def mounting(site: Optional[str] = None) -> Dict[str, object]:
    return SITE_MOUNTING[normalize_site(site if site is not None else active_site())]


def caption(site: Optional[str] = None) -> str:
    """One-line header caption: where the pod is, and the comparison rule."""
    resolved = normalize_site(site if site is not None else active_site())
    return (
        f"WORN: {SITE_LABELS[resolved]} - keep one site per session, "
        "and start a new baseline if the site changes"
    )


def measurement_summary(channel: str, site: Optional[str] = None) -> str:
    """One line combining the meaning and the first limit, for UI captions."""
    resolved = normalize_site(site if site is not None else active_site())
    note = channel_note(channel, resolved)
    first_limit = note["limits"][0] if note["limits"] else ""
    return f"{site_label(resolved)} - {note['meaning']} Limit: {first_limit}"


def guide_text(site: Optional[str] = None) -> str:
    """Printable guide for one site."""
    resolved = normalize_site(site if site is not None else active_site())
    lines = [f"WEAR SITE: {site_label(resolved)}", ""]
    mount = mounting(resolved)
    lines.append(f"Strap: {mount['strap']}")
    lines.append("")
    lines.append("Pod orientation and probe:")
    lines.extend(f"  - {item}" for item in mount["pod_orientation"])
    lines.append("")
    lines.append("Watch out for:")
    lines.extend(f"  - {item}" for item in mount["watch_out_for"])
    lines.append("")
    lines.append("Measurements on this site:")
    for channel in CHANNELS:
        note = channel_note(channel, resolved)
        lines.append(f"  {channel}: {note['meaning']}")
        for limit in note["limits"]:
            lines.append(f"      limit: {limit}")
    lines.append("")
    lines.append(CROSS_SITE_RULE)
    lines.append(
        "Educational research prototype: these are physiological trends with explicit "
        "limits, not clinical measurements."
    )
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if args and args[0] == "--both":
        for site in WEAR_SITES:
            print(guide_text(site))
            print("-" * 72)
        return 0
    try:
        print(guide_text(args[0] if args else None))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover - manual use
    raise SystemExit(main())
