---
name: design-reference-miner
description: Build, refresh, and apply a persistent local library of premium web design references. Use when Codex is asked to create or redesign a website/app using references from Awwwards, Dribbble, Dark Design, ShaderGradient, Moncy, Naresh Khatri, 3D portfolio sites, Durves, CallToInspiration, Omma, or similar sites; when the user asks to extract/recycle public code, screenshots, visual systems, motion ideas, layouts, colors, typography, interactions, or UI patterns before designing.
---

# Design Reference Miner

## Core Rule

Before creating or redesigning a visual website/app from references, mine the reference library first. Do not rely only on memory or generic taste.

Use this skill to:
- Refresh screenshots and public page data from the configured reference sites.
- Read the generated summary before design work.
- Recreate patterns from scratch using public observable behavior, layout, CSS ideas, colors, typography, and interaction patterns.
- Avoid copying a full proprietary site, brand identity, or unique source wholesale.

## Workflow

1. If references need refreshing, run `scripts/mine_refs.py`.
2. Read `references/reference-sites.md` for the source list and extraction priority.
3. Read the generated summary at the output folder, usually `C:/projeto_ai/design-reference-library/summary.md`.
4. Inspect screenshots in the output folder for the sites closest to the task.
5. Apply patterns selectively:
   - structure from Awwwards / Naresh / Omma
   - dark premium atmosphere from Dark Design
   - motion/3D hero ideas from Moncy / 3D portfolio / Omma
   - microinteractions from CallToInspiration
   - UI polish and cards from Dribbble
6. Build original code in the current project. Treat extracted code as reference material, not a direct copy target.

## Commands

Refresh the full library:

```powershell
python "C:/Users/José Victor/.codex/skills/design-reference-miner/scripts/mine_refs.py"
```

Refresh into a custom folder:

```powershell
python "C:/Users/José Victor/.codex/skills/design-reference-miner/scripts/mine_refs.py" --out "C:/projeto_ai/design-reference-library"
```

Only mine selected sites:

```powershell
python "C:/Users/José Victor/.codex/skills/design-reference-miner/scripts/mine_refs.py" --only dark_design,omma_build,moncy
```

## Output Files

The scraper writes:
- `summary.md`: concise findings and usage notes.
- `scraped.json`: structured data for all sites.
- `<site>/desktop.png` and `<site>/mobile.png`: screenshots.
- `<site>/page.html`: public rendered HTML snapshot.
- `<site>/extract.json`: colors, fonts, headings, buttons, links, sections, assets.
- `<site>/assets.txt`: discovered CSS/JS/image/font URLs.
- `<site>/css/`: downloaded same-origin or publicly accessible CSS where possible.

## Design Guardrails

- For e-commerce, prefer clear product hierarchy over excessive effects.
- For rustic/luxury, use real material cues sparingly: wood, leather, brass/amber, stitching, paper labels, shadows.
- Do not make fake glass shards, random gradients, or noisy procedural backgrounds when the user asks for clean premium design.
- On mobile, keep sticky filters compact and product cards dominant.
- Use motion only when it helps product desirability or navigation.

## Legal / Quality Boundary

It is okay to inspect public HTML/CSS/JS and use observable patterns as references. Do not clone a complete site or copy unique brand assets/text directly. Rebuild original components that fit the user's brand.
