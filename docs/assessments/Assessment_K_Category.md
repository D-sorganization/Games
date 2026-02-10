# Assessment K: Reproducibility & Provenance


## Reproducibility Audit

| Component    | Deterministic? | Seed Controlled? | Notes |
| ------------ | -------------- | ---------------- | ----- |
| Game Logic   | ✅             | ❌               | RNG used |
| Assets       | ✅             | N/A              | Static |


## Remediation Roadmap

**48 hours:** Document RNG usage.
**2 weeks:** Add seed control for deterministic runs (replay).
**6 weeks:** Full replay system.
