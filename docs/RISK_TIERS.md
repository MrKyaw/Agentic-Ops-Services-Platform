# Risk tiering (CP-2)

| Tier | Criteria | Required controls |
|---|---|---|
| low | Read-only, reversible, internal data | Peer review + eval gates |
| medium | Writes with approval, customer-adjacent data | + SME review, two-person model promotion, SoD on high-risk prompts |
| high | Irreversible/high-impact, regulated data | + risk/compliance sign-off, human-in-the-loop mandatory, completed PIA |

Tiers recorded on agents (`manifest.riskTier`), prompts (`risk`), models (`risk_tier`).
High-risk prompt approval by the author is rejected (SoD, tested). Tier changes are audited.
