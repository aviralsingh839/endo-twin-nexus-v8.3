# ULTRASOUND PIPELINE - V8.3

## Overview

Keep V8.1 ultrasound pipeline, do not pretend system has large clinically labelled dataset if not.

Extract structured features where possible, maintain provenance.

## Provenance

```
source image
→ preprocessing
→ detected features
→ quality
→ uncertainty
```

If feature cannot be reliably extracted: return UNKNOWN, never invent.

## Quality Gate

- Image quality check first (blur, brightness, etc.)
- If quality too low: withhold features, show banner
- Quality score 0..1

## Structured Features

- Largest cyst (mm): `us_cyst_size_mm` or `cyst_size_mm`
- Ovarian volume (cc): `us_volume_cc` or `volume_cc`
- Morphology: `us_morphology` or `morphology` - string or UNKNOWN

## Provenance Labels

- **CLINICALLY-ENTERED**: User manually enters structured feature (e.g. from radiology report)
- **IMAGE-DERIVED**: System extracts from image via CV (quality-gated, requires validated dataset)
- **UNKNOWN**: Feature not available, stays UNKNOWN by design until validated labelled dataset exists

## Current Status - V8.3

- Quality gate works on real images today
- Structured features UNKNOWN by design until validated, labelled, patient-grouped dataset exists
- Nothing is invented
- Clinically-entered path works: user enters cyst size, marked CLINICALLY-ENTERED, quality 0.85, used in fusion
- Image-derived path: placeholder, returns UNKNOWN unless model exists

## Fusion Integration

```python
fusion_engine.add_ultrasound(ctx, us={
  "cyst_size_mm": 5,
  "source": "CLINICALLY-ENTERED",  # or IMAGE-DERIVED
  "quality": 0.85
})
```

- Group: ultrasound
- Provenance preserved
- Weight: 0.20 if present, normalized with other groups
- Missing ultrasound → weight 0, does not drag estimate down, but absence visible

## PCOS Module Integration

- Ultrasound weight 20% if present
- Explanation includes "Includes clinically-entered ultrasound features" or "Includes image-derived..."
- Domain scores unchanged, but provenance breakdown shows ultrasound influence
- Limitations: "Ultrasound features are UNKNOWN by design until validated labelled dataset exists"

## Safety

- No ultrasound image is converted into diagnosis
- No cyst-rupture prediction exists or is claimed
- Medical safety: PCOS diagnosis requires clinician and Rotterdam criteria
- Every ultrasound feature is research estimate, not measurement unless provenance MEASURED (which ultrasound never is - it's CLINICALLY-ENTERED or IMAGE-DERIVED)

## Testing

- `test_ultrasound_provenance` verifies CLINICALLY-ENTERED vs IMAGE-DERIVED preserved
- Quality gate tested on real images (if available)
- UNKNOWN handling: returns UNKNOWN, never invents

## Future Work

- Need validated, labelled, patient-grouped ultrasound dataset
- Patient-level split (same patient not in train and test)
- Train CV model to extract structured features
- Until then, UNKNOWN by design

## Data Storage

- `data/ultrasound/` - images and structured features, labelled REAL or CLINICAL
- HistoryStore: ultrasound_history() rows with cyst_size_mm, volume_cc, morphology, source, quality
- FusionContext: ultrasound group features with provenance

## UI

- Ultrasound tab: shows features, quality, provenance, note about UNKNOWN by design
- Add button: "Add Ultrasound (Clinically Entered)" with cyst size spinbox
- Text: "Image-derived features are UNKNOWN by design until validated labelled dataset exists. This entry is clinically-entered structured feature."
