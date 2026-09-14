---
name: alphaclip-disclaimers
description: >
  Financial-content and copyright disclaimer templates for AlphaClip Forge.
  Use whenever a clip, caption, description, or schedule payload mentions
  tokens, yields, liquidations, wallets, or protocols.
---

# AlphaClip financial-content disclaimers

AlphaClip forges entertainment/education clips. It is **not** a research desk.
Every export already burns a preset disclaimer; this skill is for descriptions,
comments, and scheduler text.

## Always include

1. **Not financial advice.** No buy/sell/hold recommendation.
2. **You can lose everything.** Volatility, smart-contract, and custody risk.
3. **Do your own research.** Verify on official docs / your own node / a hardware wallet.
4. **Rights.** The operator must own or have a license to the source media.
5. **Accuracy.** Captions and hooks are machine-generated and can be wrong.

## Templates (copy, then trim to platform length)

### Shorts / TikTok description (hard cap ~300)

```
Not financial advice. Crypto is volatile — you can lose the entire stack.
Educational / entertainment only. I own or licensed this source. Captions
may be wrong. DYOR. Not a rec to buy, sell, or use any asset or protocol.
```

### YouTube description footer

```
DISCLAIMER
This video is not financial, legal, or tax advice and is not an offer to
buy or sell any security, token, or protocol interest. Digital assets are
highly volatile and can go to zero. Protocol mechanics, fees, and risks
change. Do your own research and verify contracts, URLs, and approvals
yourself.

COPYRIGHT
The operator of AlphaClip Forge represents they own the source recording
or have a license / fair-use basis to clip it. AlphaClip does not grant
rights to third-party YouTube, X, or Loom media.

#NotFinancialAdvice
```

### Wallet-security addendum

```
Security tips are educational, not a guarantee. Drainers and phishing kits
evolve. Never type a seed phrase into a website or screenshot. Verify the
domain and the spender address before you sign. AlphaClip is not liable
for lost funds.
```

### Protocol-explainer addendum

```
Mechanics here are a snapshot and may be incomplete. Read the official
docs, audits (and their scope), and oracle / upgrade / admin assumptions
before depositing. Yield figures, if shown, are not promises.
```

### Trench-recap addendum

```
On-chain drama, liquidations, and memecoin tape are not signals. Past
prints are not future results. If you feel pressure to ape, close the app.
```

### Scheduler / Buffer / Late payload

Append the short template after the hook + CTA. Never strip it to “fit more
alpha.” If the platform truncates, keep NFA + “you can lose everything” first.

## Refuse to write

- Price targets or “this will 10x”
- Fake testimonials or invented P&L
- Instructions that bypass a wallet confirmation warning
- Copy that implies AlphaClip auto-posts to a 24-channel farm

v1 schedule hooks are **dry-run unless** `BUFFER_*` / `LATE_*` keys are set
*and* the operator passes `--live`.
