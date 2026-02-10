# Assessment D: User Experience & Developer Journey


## Time-to-Value Metrics

| Stage             | Time (P50) | Time (P90) | Blockers Found |
| ----------------- | ---------- | ---------- | -------------- |
| Installation      | 5 min      | 15 min     | 1 (Dependencies) |
| First run         | 1 min      | 5 min      | 0 |
| First result      | 2 min      | 10 min     | 0 |
| Understand output | 5 min      | 10 min     | 1 (UI clarity) |


## Friction Point Heatmap

| Stage     | Friction Points | Severity | Fix Effort |
| --------- | --------------- | -------- | ---------- |
| Install   | `pip install` failures on Windows | Major | 1d |
| Custom workflow | Adding new game is undocumented | Critical | 2d |


## User Journey Map

[Install] → 😐 (Requires python knowledge)
[First run] → 😊 (Launcher works)
[Learn concepts] → 😐 (Lack of docs)
[Custom workflow] → 😡 (Undocumented)


## Remediation Roadmap

**48 hours:**
- Add `requirements.txt` with pinned versions.
- Add "Troubleshooting" section to README.

**2 weeks:**
- Create a "How to add a game" tutorial.

**6 weeks:**
- Create video walkthroughs.


## Scorecard

| Category              | Score (0-10) | Evidence | Remediation |
| --------------------- | ------------ | -------- | ----------- |
| Installation Ease     | 7            | Standard pip | Add setup script |
| First-Run Success     | 8            | Works mostly | Better error msg |
| Documentation Quality | 5            | Gaps exists | Write docs |
| Error Clarity         | 6            | Stack traces | Custom exceptions |
| API Ergonomics        | 6            | N/A | N/A |
| **Overall UX Score**  | **6.4**      | - | - |
