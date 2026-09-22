# ENDO-TWIN V8.6.1 — UI System

## Design direction

The V8.6.1 interface is based on the supplied multi-screen ENDO-TWIN case-study image and additional open-source healthcare dashboard patterns.

The goal is a **clinical research operating system** rather than a generic hospital EMR or sci-fi dashboard.

Reference patterns researched:
- MITRE Open Health Dashboard for dense multi-panel information architecture; Apache-2.0 licensed. https://github.com/mitre/OpenHealthDashboard
- manticarodrigo/health-dashboard for dashboard/card/chart patterns; MIT licensed. https://github.com/manticarodrigo/health-dashboard
- Google Android Material 3 guidance for adaptive navigation; larger screens should use a navigation rail rather than forcing bottom navigation across all form factors. https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns

The project implementation does not import code from these repositories. Their publicly documented component patterns were used as design research.

## Visual system

Primary surfaces:
- charcoal/navy application background
- lighter slate cards
- muted blue-gray borders
- lavender/periwinkle primary interface accent
- teal/emerald active/healthy state
- amber caution state
- coral/red error state

The top application bar uses a lighter lavender/slate field to create the same high-level visual anchor seen in the reference board.

## Doctor desktop

Core flow:

**Dashboard → Patients → Patient workspace**

Patient workspace tabs:

**Overview · Timeline · Sensor Data · Trends/Physiology · Ultrasound · AI/Models · Clinical Inputs · Reports · Notes · Provenance · Audit**

The selected patient remains visible in the header so that changing context is deliberate.

The Doctor dashboard emphasizes:
- active patient count
- review queue
- data-quality distribution
- current flags/context
- recently synced patients
- compact physiological trend views

Synthetic demo tiers are visibly marked as DEMO_DATA and are never presented as clinical severity.

## Patient desktop

Core flow:

**Overview · My Health · Measurements · Timeline · Reports · Connect · Notes**

The patient interface is deliberately calmer:
- personal baseline
- repeated measurements
- trend cards
- provenance badges
- simple explanations
- local report workflow
- patient-scoped notes

Disease-model output is not visually mixed into routine measurements.

## Android

Phone:
- bottom navigation for primary destinations
- vertically stacked cards
- horizontally scrollable secondary filters
- large touch targets

Large-screen Android:
- adaptive NavigationRail
- same content hierarchy as the phone version
- patient context stays visible
- denser cards/charts without simply stretching the phone UI

This follows current Material guidance that large screens should use a rail/navigation pattern rather than a forced bottom navigation layout.

## Component rules

Metric cards contain:
- metric name
- large value
- short interpretation/context
- provenance badge
- trend when available

Status badges use semantics:
- measured
- derived
- warning
- error
- neutral
- research/model

Do not use colour as the only semantic indicator.

## Scientific UI rules

Every value must keep its evidence boundary visible.

Example:

**88 bpm · MEASURED**

**31 ms · DERIVED**

**CHRONO-PCOS · MODEL-INFERRED**

**UNKNOWN · insufficient evidence**

A synthetic demo value is shown as:

**88 bpm · DEMO_DATA**

The interface must never imply that:
- a wearable diagnoses PCOS;
- a heuristic research index is a clinical probability;
- an uploaded ultrasound automatically yields anatomical findings;
- an engineering quality score equals clinical validity.

## Ultrasound surface

The imaging panel supports source attachment/preview while maintaining explicit unknown states for unsupported features.

No anatomical feature is filled with a plausible-looking value merely to make the UI visually complete.

## Reporting surface

Report order:

**Patient → Acquisition → Quality → Features → Baseline → Longitudinal Context → Model → Uncertainty → Limitations**

This ordering makes it difficult for a model result to visually masquerade as a raw observation.

## Privacy and scope

Patient selection controls the entire patient workspace context.

The desktop implementation is local-first. The current mobile bridge is trusted-LAN research infrastructure, not production health-system security.

## Design acceptance checklist

Before releasing a UI change:

- demo/live status is visible;
- patient scope is visible;
- provenance is visible;
- missing/unknown states are visible;
- model status and validation status are visible;
- no synthetic value looks like a measured clinical record;
- phone and large-screen navigation are appropriate to form factor;
- charts have bounded data histories;
- colours support hierarchy without becoming decorative noise.
