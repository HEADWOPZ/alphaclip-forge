---
name: alphaclip-hooks
description: >
  Generate Shorts/TikTok title and hook variants for AlphaClip Forge crypto clips.
  Use when writing titles, on-screen hooks, or A/B copy for trench recaps,
  protocol explainers, or wallet-security tips.
---

# AlphaClip hook & title variants

Write **6–8 options** for a clip cut from a crypto source. Stay inside the
preset voice. Never promise returns. Never invent facts that are not in the
transcript excerpt.

## Inputs you should ask for (or infer)

- `preset`: `trench-recap` | `protocol-explainer` | `wallet-security-tip`
- `excerpt`: transcript text for this cut
- `reasons`: scorer keywords (optional)
- `duration`: seconds (usually 10–32)

## Voice by preset

| Preset | Voice | Forbidden |
| --- | --- | --- |
| trench-recap | Fast, dry, tape-literate. One image per line. | Price targets, “easy money”, calls to ape |
| protocol-explainer | Calm teacher. Mechanism first. | “Risk-free yield”, unaudited-as-safe |
| wallet-security-tip | Stern, specific, actionable. | Fear-mongering without a concrete tell |

## Output format

```md
## Hooks (spoken / on-screen, ≤ 12 words)
1. ...
2. ...

## Titles (feed, ≤ 70 chars)
1. ...
2. ...

## Why these work
- One line on pattern (curiosity gap, specificity, contrast)
```

## Patterns that convert without lying

- Specificity: “three liquidations”, “unlimited USDC approval”, “the sequencer pause”
- Contrast: slept vs printed, docs vs the actual flow
- Time box: “in 15 seconds”, “before you deposit”
- Second person, one subject

## Anti-patterns

- All-caps spam, rocket/moon emoji walls
- “Guaranteed”, “risk-free”, “generational wealth incoming”
- Naming a token as a buy
- Inventing a dollar figure not in the excerpt

If the excerpt is thin, say so and write *generic-but-honest* hooks from the
preset library in `alphaclip/presets.py` instead of hallucinating a narrative.

Pair every pack with the `alphaclip-disclaimers` skill.
