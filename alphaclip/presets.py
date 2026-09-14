from __future__ import annotations

from alphaclip.models import Preset

NFA = (
    "Not financial advice. Crypto is volatile and you can lose everything. "
    "This is entertainment / education, not a recommendation to buy, sell, or use any asset."
)

TRENCH = Preset(
    id="trench-recap",
    name="Trench Recap",
    description="High-energy overnight recap: liquidations, runners, rugs, and bags.",
    hooks=[
        "The trenches printed while you slept.",
        "This wallet just got absolutely wrecked.",
        "If you blinked you missed the runner.",
        "Don't fade this tape.",
        "One chart. Three liquidations. Zero sympathy.",
    ],
    title_templates=[
        "This {topic} move is unhinged",
        "Trench recap: {topic}",
        "You slept on {topic}",
        "{topic} just nuked the tape",
        "POV: you faded {topic}",
    ],
    cta="Follow for daily trench recaps — next clip in the stack.",
    disclaimer=NFA + " On-chain drama is not a signal.",
    keywords={
        "airdrop": 2.4,
        "liquidation": 2.8,
        "liquidated": 2.8,
        "cascade": 2.2,
        "rug": 2.6,
        "rugged": 2.6,
        "whale": 2.0,
        "runner": 2.3,
        "pumped": 1.8,
        "nuked": 2.2,
        "short": 1.4,
        "long": 1.2,
        "leverage": 2.0,
        "funding": 1.6,
        "open interest": 2.0,
        "oi": 1.2,
        "bag": 1.6,
        "bags": 1.6,
        "trench": 2.0,
        "trenches": 2.0,
        "memecoin": 2.0,
        "degen": 1.8,
        "ape": 1.5,
        "aped": 1.6,
        "pump": 1.7,
        "dump": 1.7,
        "wick": 1.5,
        "squeeze": 2.0,
        "generational": 2.1,
    },
    target_duration=16.0,
    min_duration=10.0,
    max_duration=28.0,
    caption_fill="&H00F4F7FF",
    cta_fill="&H0000D4FF",
    accent_hex="F0B429",
)

PROTOCOL = Preset(
    id="protocol-explainer",
    name="Protocol Explainer",
    description="Plain-language how-it-works clips for L2s, DEXes, restaking, and vaults.",
    hooks=[
        "Here's how this protocol actually works.",
        "Stop aping until you understand this flow.",
        "The mechanism in 20 seconds.",
        "This is the part the docs bury.",
        "Save this before you deposit.",
    ],
    title_templates=[
        "How {topic} actually works",
        "{topic} in 20 seconds",
        "The {topic} flow nobody explains",
        "Don't deposit into {topic} until this",
        "{topic}, without the jargon",
    ],
    cta="Save this. Read the docs. Then decide — not the other way around.",
    disclaimer=NFA + " Protocol mechanics change. Verify on official docs and your own node/UI.",
    keywords={
        "protocol": 2.2,
        "mechanism": 2.0,
        "liquidity": 1.8,
        "pool": 1.4,
        "amm": 2.0,
        "order book": 1.8,
        "rollup": 2.0,
        "l2": 1.6,
        "restake": 2.2,
        "restaking": 2.2,
        "validator": 1.8,
        "slash": 2.0,
        "slashing": 2.0,
        "tvl": 2.0,
        "yield": 1.8,
        "apr": 1.7,
        "apy": 1.7,
        "vault": 1.6,
        "collateral": 1.8,
        "oracle": 2.0,
        "bridge": 1.8,
        "intent": 1.5,
        "sequencer": 1.8,
        "finality": 1.8,
        "gas": 1.3,
        "fee": 1.2,
        "governance": 1.6,
        "token": 1.1,
        "stake": 1.5,
        "deposit": 1.6,
        "withdraw": 1.5,
    },
    target_duration=20.0,
    min_duration=12.0,
    max_duration=32.0,
    caption_fill="&H00FFFFFF",
    cta_fill="&H00B8FF7A",
    accent_hex="7DFFB3",
)

SECURITY = Preset(
    id="wallet-security-tip",
    name="Wallet Security Tip",
    description="Drainers, approvals, seed phrases, hardware wallets — short and stern.",
    hooks=[
        "This drain trick is everywhere right now.",
        "If you signed this, assume you're cooked.",
        "Revoke that approval before you sleep.",
        "Your seed phrase is not a backup meme.",
        "Hardware wallet or you're the exit liquidity.",
    ],
    title_templates=[
        "Stop getting drained by {topic}",
        "Wallet tip: {topic}",
        "This {topic} trick empties wallets",
        "Do this before you sign {topic}",
        "{topic} — 15 seconds that save a bag",
    ],
    cta="Lock this in. Share it with the group chat before they sign.",
    disclaimer=(
        NFA + " Security tips are educational, not a guarantee. "
        "Phishing and drainers evolve. Verify URLs and contracts yourself."
    ),
    keywords={
        "drain": 2.8,
        "drainer": 2.8,
        "drained": 2.8,
        "phish": 2.6,
        "phishing": 2.6,
        "seed phrase": 2.8,
        "seed": 1.8,
        "recovery phrase": 2.6,
        "private key": 2.6,
        "approval": 2.4,
        "approve": 2.2,
        "revoke": 2.4,
        "permit": 2.2,
        "signature": 2.0,
        "signed": 1.8,
        "sign": 1.4,
        "hardware wallet": 2.4,
        "ledger": 2.0,
        "trezor": 2.0,
        "clipboard": 2.0,
        "malware": 2.2,
        "extension": 1.6,
        "walletconnect": 1.8,
        "blind sign": 2.4,
        "blind signing": 2.4,
        "spoof": 2.2,
        "address": 1.3,
        "allowance": 2.2,
        "unlimited": 2.0,
        "connector": 1.5,
        "site": 1.1,
    },
    target_duration=15.0,
    min_duration=10.0,
    max_duration=26.0,
    caption_fill="&H00F5F0FF",
    cta_fill="&H007A8CFF",
    accent_hex="FF6B6B",
)

PRESETS: dict[str, Preset] = {
    TRENCH.id: TRENCH,
    PROTOCOL.id: PROTOCOL,
    SECURITY.id: SECURITY,
}


def list_presets() -> list[Preset]:
    return list(PRESETS.values())


def get_preset(preset_id: str) -> Preset:
    key = (preset_id or "").strip().lower()
    if key not in PRESETS:
        known = ", ".join(PRESETS)
        raise ValueError(f"Unknown preset '{preset_id}'. Choose one of: {known}")
    return PRESETS[key]
