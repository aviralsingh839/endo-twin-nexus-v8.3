# ENDO-TWIN NEXUS UI Design System

## Design intent

Clinical, research-grade, precise, calm, technical and information-dense. The system deliberately avoids neon, gradients, glassmorphism, giant cards, excessive shadows and decorative dashboards.

## Core palette

- Ink: #17212B
- Muted ink: #667483
- Canvas: #F6F8FB
- Surface: #FFFFFF
- Surface alternate: #F9FBFD
- Border: #D8E0E8
- Strong border: #C5CFDA
- Teal: #0B6670
- Teal strong: #167D88
- Deep teal: #0B5962
- Research blue: #315B84
- Research violet: #6D628A
- Success: #237A57
- Warning: #A66A00
- Error: #B33A3A

## Radius policy

- 4px: compact controls
- 6px: buttons, inputs, small badges
- 8px: primary panels
- 10px maximum for large containers
- Pills are reserved for statuses/provenance, not general content containers.

## Spacing

Use a 4px base rhythm: 4, 8, 12, 16, 20, 24, 32, 40.

Desktop content should favor compact 12–20px panel padding. Mobile should favor 12–16dp content padding.

## Typography

Use Inter/Segoe UI/Noto Sans fallback stacks. Titles are bold, but body copy stays regular. Labels use restrained uppercase tracking only for metadata/eyebrows.

## Semantic status

LIVE = teal/green semantic state.
DEMO = amber semantic state.
MEASURED = teal.
DERIVED = blue/violet.
MODEL = violet/blue and always accompanied by provenance.
UNAVAILABLE = neutral gray.
ERROR = red.

Never communicate state by color alone: pair color with text/icon.

## Charts

Use a stable channel palette, meaningful units, timestamps and signal-quality overlays. Avoid decorative pie charts or rainbow palettes. Missing channels remain unavailable rather than being filled with fabricated values.

## Interaction

Hover and pressed states are subtle. Focus rings must remain visible. Motion is short and functional. Reduced-motion preferences must be respected where the platform supports them.

## Shared surface vocabulary

Every major surface should answer: Where am I? What data am I viewing? Where did it come from? Is it LIVE or DEMO? What is the next useful action?

## Design direction (V8.6.1 research notes)

The interface aims at a **clinical research operating system**, not a generic
hospital EMR and not a sci-fi dashboard. Patterns were researched from MITRE
Open Health Dashboard (Apache-2.0), manticarodrigo/health-dashboard (MIT) and
current Material 3 guidance for adaptive navigation. No code was imported; only
publicly documented component patterns informed the layout.

## Per-surface flows

**Doctor desktop:** Dashboard → Patients → patient workspace
(Overview · Timeline · Sensor Data · Trends/Physiology · Ultrasound · AI/Models ·
Clinical Inputs · Reports · Notes · Provenance · Audit). The selected patient stays
visible in the header so changing context is deliberate.

**Patient desktop:** Overview · My Health · Measurements · Timeline · Reports ·
Connect · Notes - calmer, baseline-first, with provenance badges and simple
explanations. Disease-model output is never mixed into routine measurements.

**Android:** phone uses bottom navigation with stacked cards and large touch
targets; large screens use an adaptive navigation rail with the same content
hierarchy rather than a stretched phone layout.

## Component rules

Metric cards carry: name, large value, short interpretation, provenance badge and
trend when available. Status badges use the semantics measured / derived / warning
/ error / neutral / research-model, and colour is never the only indicator.

## Scientific UI rules

Every value keeps its evidence boundary visible - "88 bpm · MEASURED",
"31 ms · DERIVED", "CHRONO-PCOS · MODEL-INFERRED", "UNKNOWN · insufficient
evidence", "88 bpm · DEMO_DATA". The interface must never imply that a wearable
diagnoses PCOS, that a heuristic research index is a clinical probability, that an
uploaded ultrasound yields anatomical findings, or that an engineering quality
score equals clinical validity.

Reports are ordered **Patient → Acquisition → Quality → Features → Baseline →
Longitudinal Context → Model → Uncertainty → Limitations** so a model result cannot
visually masquerade as a raw observation. Unsupported imaging features stay
explicitly unknown; no plausible-looking value is filled in to complete a panel.

## Design acceptance checklist

Before releasing a UI change: demo/live status visible; patient scope visible;
provenance visible; missing/unknown states visible; model and validation status
visible; no synthetic value looks like a measured record; navigation suits the form
factor; charts have bounded histories; colour supports hierarchy without decoration.
