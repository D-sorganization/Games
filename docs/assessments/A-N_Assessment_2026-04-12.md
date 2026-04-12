# A-N Assessment - Games - 2026-04-12

Run time: 2026-04-12T08:06:46.6052936Z UTC
Sync status: blocked
Sync notes: stash failed: warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
warning: could not open directory '.pytest_cache/': Permission denied
warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
warning: could not open directory '.pytest_cache/': Permission denied
warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
Saved working directory and index state On remediation-wave-1775915370: automation-sync-2026-04-12
warning: unable to access 'C:\Users\diete/.config/git/ignore': Permission denied
warning: could not open directory '.pytest_cache/': Permission denied
warning: failed to remove .pytest_cache/: Directory not empty

Overall grade: C (75/100)

## Coverage Notes
- Reviewed tracked first-party files from git ls-files, excluding cache, build, vendor, virtualenv, and generated output directories.
- Reviewed 752 tracked files, including 359 code files, 138 test files, 30 CI files, 7 config/build files, and 127 docs/onboarding files.
- This is a read-only static assessment of committed files. TDD history and Law of Demeter semantics cannot be fully confirmed without commit-by-commit workflow review and deeper call-graph analysis.

## Category Grades
### A. Architecture and Boundaries: B (82/100)
Evaluates whether first-party code is organized into clear source boundaries.
- Evidence: `752 tracked first-party files`
- Evidence: `471 files under source-like directories`

### B. Build and Dependency Management: B (84/100)
Evidence comes from tracked build, dependency, and tool configuration files.
- Evidence: `CMakeLists.txt`
- Evidence: `pyproject.toml`
- Evidence: `requirements.txt`
- Evidence: `ruff.toml`
- Evidence: `src/games/QuatGolf/CMakeLists.txt`
- Evidence: `src/games/Wizard_of_Wor/wizard_of_wor/requirements.txt`
- Evidence: `src/games/shared/cpp/CMakeLists.txt`

### C. Configuration and Environment Hygiene: C (78/100)
Checks whether runtime/build configuration is explicit and committed.
- Evidence: `CMakeLists.txt`
- Evidence: `pyproject.toml`
- Evidence: `requirements.txt`
- Evidence: `ruff.toml`
- Evidence: `src/games/QuatGolf/CMakeLists.txt`
- Evidence: `src/games/Wizard_of_Wor/wizard_of_wor/requirements.txt`
- Evidence: `src/games/shared/cpp/CMakeLists.txt`

### D. Contracts, Types, and Domain Modeling: B (82/100)
Covers Design by Contract signals: validation, asserts, typed models, and explicit invariants.
- Evidence: `game_launcher.py`
- Evidence: `run_tests.py`
- Evidence: `scripts/analyze_completist_data.py`
- Evidence: `scripts/create_issues_from_assessment.py`
- Evidence: `scripts/generate_assessment_summary.py`
- Evidence: `scripts/mypy_autofix_agent.py`
- Evidence: `scripts/run_assessment.py`
- Evidence: `scripts/setup_hooks.py`

### E. Reliability and Error Handling: C (76/100)
Reliability grade is based on tests plus explicit validation/error handling evidence.
- Evidence: `.agent/skills/tests/SKILL.md`
- Evidence: `.claude/skills/tests/SKILL.md`
- Evidence: `docs/assessments/Assessment_C_Test_Coverage.md`
- Evidence: `docs/assessments/archive/Assessment_C_Test_Coverage.md`
- Evidence: `src/games/Duum/tests/__init__.py`
- Evidence: `game_launcher.py`
- Evidence: `run_tests.py`
- Evidence: `scripts/analyze_completist_data.py`

### F. Function, Module Size, and SRP: F (55/100)
Evaluates function size, module size, and single responsibility using coarse static size signals.
- Evidence: `scripts/mypy_autofix_agent.py (623 lines)`
- Evidence: `scripts/run_assessment.py (521 lines)`
- Evidence: `src/games/Force_Field/src/combat_system.py (512 lines)`
- Evidence: `src/games/QuatGolf/src/main.cpp (738 lines)`
- Evidence: `src/games/shared/combat_manager.py (533 lines)`
- Evidence: `src/games/shared/bot_base.py (coarse avg 89 lines/definition)`
- Evidence: `src/games/shared/renderers/baby_renderer.py (coarse avg 81 lines/definition)`
- Evidence: `src/games/shared/renderers/cyber_demon_renderer.py (coarse avg 127 lines/definition)`

### G. Testing and TDD Posture: B (82/100)
TDD cannot be confirmed from static files alone; grade reflects committed automated test posture.
- Evidence: `.agent/skills/tests/SKILL.md`
- Evidence: `.claude/skills/tests/SKILL.md`
- Evidence: `docs/assessments/Assessment_C_Test_Coverage.md`
- Evidence: `docs/assessments/archive/Assessment_C_Test_Coverage.md`
- Evidence: `src/games/Duum/tests/__init__.py`
- Evidence: `src/games/Duum/tests/test_bot.py`
- Evidence: `src/games/Duum/tests/test_entity_manager.py`
- Evidence: `src/games/Duum/tests/test_fps.py`
- Evidence: `src/games/Duum/tests/test_game_logic.py`
- Evidence: `src/games/Duum/tests/test_managers.py`

### H. CI/CD and Automation: C (78/100)
Checks for tracked continuous integration or automation workflows.
- Evidence: `.github/workflows/Bot-CI-Trigger.yml`
- Evidence: `.github/workflows/Jules-Auto-Assign-Issues.yml`
- Evidence: `.github/workflows/Jules-Auto-Rebase.yml`
- Evidence: `.github/workflows/Jules-Auto-Refactor.yml`
- Evidence: `.github/workflows/Jules-Auto-Repair.yml`
- Evidence: `.github/workflows/Jules-Cleaner.yml`
- Evidence: `.github/workflows/Jules-Code-Quality-Fixer.yml`
- Evidence: `.github/workflows/Jules-Control-Tower.yml`

### I. Security and Secret Hygiene: B (82/100)
Secret scan is regex-based and should be followed by dedicated secret scanning for confirmation.
- Evidence: No direct tracked-file evidence found for this category.

### J. Documentation and Onboarding: B (82/100)
Checks whether docs and onboarding files are present.
- Evidence: `.Jules/palette.md`
- Evidence: `.agent/skills/issues-10-sequential/SKILL.md`
- Evidence: `.agent/skills/issues-5-combined/SKILL.md`
- Evidence: `.agent/skills/lint/SKILL.md`
- Evidence: `.agent/skills/tests/SKILL.md`
- Evidence: `.agent/skills/update-issues/SKILL.md`
- Evidence: `.agent/workflows/issues-10-sequential.md`
- Evidence: `.agent/workflows/issues-5-combined.md`
- Evidence: `.agent/workflows/lint.md`
- Evidence: `.agent/workflows/tests.md`

### K. Maintainability, DRY, and Duplication: F (55/100)
DRY grade uses duplicate-name clusters and TODO/FIXME density as static heuristics.
- Evidence: `constants appears in 6 files`
- Evidence: `game appears in 5 files`
- Evidence: `particle_system appears in 4 files`
- Evidence: `player appears in 4 files`
- Evidence: `projectile appears in 4 files`
- Evidence: `scripts/analyze_completist_data.py`
- Evidence: `scripts/pragmatic_programmer_review.py`
- Evidence: `scripts/shared/quality_checks_common.py`

### L. API Surface and Law of Demeter: C (70/100)
Law of Demeter requires semantic review; this run records static coverage and flags no confirmed violation without direct evidence.
- Evidence: `.ci_trigger.py`
- Evidence: `conftest.py`
- Evidence: `constants_file.py`
- Evidence: `convert_icon.py`
- Evidence: `create_better_shortcut.ps1`
- Evidence: `create_desktop_shortcut.ps1`
- Evidence: `game_launcher.py`
- Evidence: `run_tests.py`

### M. Observability and Operability: C (74/100)
Checks for logging, metrics, monitoring, or operations-oriented files.
- Evidence: `docs/assessments/Assessment_L_Logging.md`
- Evidence: `docs/assessments/archive/Assessment_L_Logging.md`
- Evidence: `scripts/shared/logging_config.py`

### N. Governance, Licensing, and Release Hygiene: C (74/100)
Checks for release, ownership, contribution, and license metadata.
- Evidence: `.github/CODEOWNERS`
- Evidence: `.github/agents/security-agent.md`
- Evidence: `CHANGELOG.md`
- Evidence: `CONTRIBUTING.md`
- Evidence: `LICENSE`
- Evidence: `SECURITY.md`
- Evidence: `docs/assessments/Assessment_F_Security.md`
- Evidence: `docs/assessments/archive/Assessment_F_Security.md`

## Key Risks
- Large modules/scripts reduce maintainability and SRP clarity.
- Repeated filename clusters suggest possible duplicated responsibilities.

## Prioritized Remediation Recommendations
1. Split the largest modules by responsibility and add characterization tests before refactoring.
2. Review duplicate filename/responsibility clusters and extract shared helpers only where behavior is truly repeated.

## Actionable Issue Candidates
### Split oversized modules by responsibility
- Severity: medium
- Problem: Oversized files found: scripts/mypy_autofix_agent.py (623 lines); scripts/run_assessment.py (521 lines); src/games/Force_Field/src/combat_system.py (512 lines); src/games/QuatGolf/src/main.cpp (738 lines); src/games/shared/combat_manager.py (533 lines); src/games/shared/cpp/tests/test_core_game_ai.cpp (625 lines); src/games/shared/cpp/tests/test_loaders.cpp (710 lines); src/games/shared/raycaster.py (727 lines); tests/shared/test_combat_manager.py (585 lines); tests/shared/test_player_base.py (594 lines); tests/tetris/test_tetris_comprehensive.py (506 lines)
- Evidence: See category evidence above.
- Impact: Large modules obscure ownership, complicate review, and weaken SRP.
- Proposed fix: Add characterization tests, then split cohesive responsibilities into smaller modules.
- Acceptance criteria: Largest files are reduced or justified; extracted modules have focused tests.
- Expectations: SRP, function size, module size, maintainability

### Review duplicated responsibility clusters
- Severity: medium
- Problem: Repeated filename clusters found: constants appears in 6 files; game appears in 5 files; particle_system appears in 4 files; player appears in 4 files; projectile appears in 4 files
- Evidence: See category evidence above.
- Impact: Potential duplicated logic increases maintenance cost and drift risk.
- Proposed fix: Review clusters, remove accidental duplication, and extract shared helpers where behavior is truly common.
- Acceptance criteria: Documented review of clusters; duplicated implementations are consolidated or justified.
- Expectations: DRY, maintainability, SRP

