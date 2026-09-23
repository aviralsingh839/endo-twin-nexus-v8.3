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
