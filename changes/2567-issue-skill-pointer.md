---
issue: 2567
summary: Replace obsolete combined-issue instructions with a canonical lane pointer.
---

## RM #2567: Canonical Issue-Work Pointer

Retain the legacy entry point as a pointer to the maintained fleet lane skill.
Remove copied batching and merge instructions; preserve current task gates.

Validation: two regressions fail before the change; focused pointer and legacy-tree tests pass after.
