# A-N Assessment - Games - 2026-04-17

Run time: 2026-04-17T08:01:19.6221680Z UTC
Sync status: blocked
Sync notes: stash failed: warning: unable to access '.pytest_cache/.gitignore': Permission denied
warning: unable to access '.pytest_cache/.gitignore': Permission denied
error: open(".pytest_cache/.gitignore"): Permission denied
fatal: Unable to process path .pytest_cache/.gitignore
Cannot save the untracked files

Overall grade: C (74/100)

## Coverage Notes
- Reviewed tracked first-party files from git ls-files, excluding cache, build, vendor, virtualenv, temp, and generated output directories.
- Reviewed 759 tracked files, including 365 code files, 142 test files, 30 CI files, 7 config/build files, and 128 docs/onboarding files.
- This is a read-only static assessment of committed files. TDD history and confirmed Law of Demeter semantics require commit-history review and deeper call-graph analysis; this report distinguishes those limits from confirmed file evidence.

## Category Grades
### A. Architecture and Boundaries: B (82/100)
Assesses source organization and boundary clarity from tracked first-party layout.
- Evidence: `759 tracked first-party files`
- Evidence: `473 files under source-like directories`

### B. Build and Dependency Management: B (84/100)
Assesses committed build, dependency, and tool configuration.
- Evidence: `CMakeLists.txt`
- Evidence: `pyproject.toml`
- Evidence: `requirements.txt`
- Evidence: `ruff.toml`
- Evidence: `src/games/QuatGolf/CMakeLists.txt`
- Evidence: `src/games/Wizard_of_Wor/wizard_of_wor/requirements.txt`
- Evidence: `src/games/shared/cpp/CMakeLists.txt`

### C. Configuration and Environment Hygiene: C (78/100)
Checks whether runtime and developer configuration is explicit.
- Evidence: `CMakeLists.txt`
- Evidence: `pyproject.toml`
- Evidence: `requirements.txt`
- Evidence: `ruff.toml`
- Evidence: `src/games/QuatGolf/CMakeLists.txt`
- Evidence: `src/games/Wizard_of_Wor/wizard_of_wor/requirements.txt`
- Evidence: `src/games/shared/cpp/CMakeLists.txt`

### D. Contracts, Types, and Domain Modeling: B (82/100)
Design by Contract evidence includes validation, assertions, typed models, explicit raised errors, and invariants.
- Evidence: `game_launcher.py`
- Evidence: `run_tests.py`
- Evidence: `scripts/analyze_completist_data.py`
- Evidence: `scripts/create_issues_from_assessment.py`
- Evidence: `scripts/generate_assessment_summary.py`
- Evidence: `scripts/mypy_autofix_agent.py`
- Evidence: `scripts/run_assessment.py`
- Evidence: `scripts/setup_hooks.py`
- Evidence: `src/contracts.py`
- Evidence: `src/games/Duum/src/atmosphere_manager.py`

### E. Reliability and Error Handling: C (76/100)
Reliability is graded from test presence plus explicit validation/error-handling signals.
- Evidence: `.agent/skills/tests/SKILL.md`
- Evidence: `.claude/skills/tests/SKILL.md`
- Evidence: `docs/assessments/Assessment_C_Test_Coverage.md`
- Evidence: `docs/assessments/archive/Assessment_C_Test_Coverage.md`
- Evidence: `src/games/Duum/tests/__init__.py`
- Evidence: `game_launcher.py`
- Evidence: `run_tests.py`
- Evidence: `scripts/analyze_completist_data.py`
- Evidence: `scripts/create_issues_from_assessment.py`
- Evidence: `scripts/generate_assessment_summary.py`

### F. Function, Module Size, and SRP: F (55/100)
Evaluates function size, script/module size, and single responsibility using static size signals.
- Evidence: `conftest.py (524 lines)`
- Evidence: `scripts/mypy_autofix_agent.py (732 lines)`
- Evidence: `scripts/run_assessment.py (629 lines)`
- Evidence: `src/games/Force_Field/src/bot.py (510 lines)`
- Evidence: `src/games/Force_Field/src/combat_system.py (612 lines)`
- Evidence: `src/games/Force_Field/src/gameplay_runtime.py (501 lines)`
- Evidence: `src/games/Force_Field/src/weapon_renderer.py (556 lines)`
- Evidence: `scripts/generate_assessment_summary.py (coarse avg 84 lines/definition)`
- Evidence: `scripts/run_all_assessments.py (coarse avg 95 lines/definition)`
- Evidence: `src/games/shared/bot_base.py (coarse avg 108 lines/definition)`

### G. Testing and TDD Posture: B (82/100)
TDD history cannot be confirmed statically; grade reflects committed automated test posture.
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
- Evidence: `src/games/Duum/tests/test_ninja.py`
- Evidence: `src/games/Duum/tests/test_particle_system.py`

### H. CI/CD and Automation: C (78/100)
Checks for tracked CI/CD workflow files.
- Evidence: `.github/workflows/Bot-CI-Trigger.yml`
- Evidence: `.github/workflows/Jules-Auto-Assign-Issues.yml`
- Evidence: `.github/workflows/Jules-Auto-Rebase.yml`
- Evidence: `.github/workflows/Jules-Auto-Refactor.yml`
- Evidence: `.github/workflows/Jules-Auto-Repair.yml`
- Evidence: `.github/workflows/Jules-Cleaner.yml`
- Evidence: `.github/workflows/Jules-Code-Quality-Fixer.yml`
- Evidence: `.github/workflows/Jules-Control-Tower.yml`
- Evidence: `.github/workflows/Jules-Documentation-Auditor.yml`
- Evidence: `.github/workflows/Jules-Hotfix-Creator.yml`

### I. Security and Secret Hygiene: B (82/100)
Secret scan is regex-based; findings require manual confirmation.
- Evidence: No direct tracked-file evidence found for this category.

### J. Documentation and Onboarding: B (82/100)
Checks docs, README, onboarding, and release documents.
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
- Evidence: `.agent/workflows/update-issues.md`
- Evidence: `.claude/skills/issues-10-sequential/SKILL.md`

### K. Maintainability, DRY, and Duplication: F (55/100)
DRY is assessed through duplicate filename clusters and TODO/FIXME density as static heuristics.
- Evidence: `constants appears in 6 files`
- Evidence: `game appears in 5 files`
- Evidence: `particle_system appears in 4 files`
- Evidence: `player appears in 4 files`
- Evidence: `projectile appears in 4 files`
- Evidence: `scripts/analyze_completist_data.py`
- Evidence: `scripts/pragmatic_programmer_review.py`
- Evidence: `scripts/shared/quality_checks_common.py`
- Evidence: `src/games/QuatGolf/src/course/CourseBuilder.h`
- Evidence: `src/games/Tetris/tests/test_tetris.py`

### L. API Surface and Law of Demeter: F (58/100)
Law of Demeter is approximated with deep member-chain hints; confirmed violations require semantic review.
- Evidence: `create_desktop_shortcut.ps1`
- Evidence: `src/games/Duum/tests/test_bot.py`
- Evidence: `src/games/Duum/tests/test_entity_manager.py`
- Evidence: `src/games/Duum/tests/test_particle_system.py`
- Evidence: `src/games/Duum/tests/test_player.py`
- Evidence: `src/games/Duum/tests/test_renderer.py`
- Evidence: `src/games/Force_Field/src/combat_system.py`
- Evidence: `src/games/Force_Field/src/game_input.py`
- Evidence: `src/games/Force_Field/tests/test_entity_manager.py`
- Evidence: `src/games/Force_Field/tests/test_fps.py`

### M. Observability and Operability: C (74/100)
Checks for logging, metrics, monitoring, and operational artifacts.
- Evidence: `docs/assessments/Assessment_L_Logging.md`
- Evidence: `docs/assessments/archive/Assessment_L_Logging.md`
- Evidence: `scripts/shared/logging_config.py`

### N. Governance, Licensing, and Release Hygiene: C (74/100)
Checks ownership, release, contribution, security, and license metadata.
- Evidence: `.github/CODEOWNERS`
- Evidence: `.github/agents/security-agent.md`
- Evidence: `CHANGELOG.md`
- Evidence: `CONTRIBUTING.md`
- Evidence: `LICENSE`
- Evidence: `SECURITY.md`
- Evidence: `docs/assessments/Assessment_F_Security.md`
- Evidence: `docs/assessments/archive/Assessment_F_Security.md`

## Explicit Engineering Practice Review
- TDD: Automated tests are present, but red-green-refactor history is not confirmable from static files.
- DRY: Duplicate responsibility clusters require review: constants appears in 6 files; game appears in 5 files; particle_system appears in 4 files; player appears in 4 files; projectile appears in 4 files
- Design by Contract: Validation/contract signals were found in tracked code.
- Law of Demeter: Deep member-chain hints were found and should be semantically reviewed.
- Function size and SRP: Large modules or coarse long-definition signals were found.

## Key Risks
- Large modules/scripts reduce maintainability and SRP clarity.
- Repeated filename clusters suggest possible duplicated responsibilities.
- Deep member-chain usage may indicate Law of Demeter pressure points.

## Prioritized Remediation Recommendations
1. Split the largest modules by responsibility and add characterization tests before refactoring.
2. Review duplicate filename/responsibility clusters and extract shared helpers only where behavior is truly repeated.
3. Review deep member chains and introduce boundary methods where object graph traversal leaks across modules.

## Actionable Issue Candidates
### Split oversized modules by responsibility
- Severity: medium
- Problem: Oversized files found: conftest.py (524 lines); scripts/mypy_autofix_agent.py (732 lines); scripts/run_assessment.py (629 lines); src/games/Force_Field/src/bot.py (510 lines); src/games/Force_Field/src/combat_system.py (612 lines); src/games/Force_Field/src/gameplay_runtime.py (501 lines); src/games/Force_Field/src/weapon_renderer.py (556 lines); src/games/Peanut_Butter_Panic/peanut_butter_panic/core.py (560 lines); src/games/QuatGolf/src/main.cpp (835 lines); src/games/shared/combat_manager.py (625 lines); src/games/shared/cpp/tests/test_core_game_ai.cpp (727 lines); src/games/shared/cpp/tests/test_loaders.cpp (866 lines); src/games/shared/fps_game_base.py (550 lines); src/games/shared/raycaster.py (824 lines); src/games/shared/raycaster_rendering.py (617 lines); tests/shared/cpp/test_math.cpp (540 lines); tests/shared/test_combat_manager.py (670 lines); tests/shared/test_player_base.py (698 lines); tests/shared/test_raycaster.py (586 lines); tests/tetris/test_tetris_comprehensive.py (657 lines)
- Evidence: Category F lists files over 500 lines or coarse long-definition signals.
- Impact: Large modules obscure ownership, complicate review, and weaken SRP.
- Proposed fix: Add characterization tests, then split cohesive responsibilities into smaller modules.
- Acceptance criteria: Largest files are reduced or justified; extracted modules have focused tests.
- Expectations: SRP, function size, module size, maintainability

### Review duplicated responsibility clusters
- Severity: medium
- Problem: Repeated filename clusters found: constants appears in 6 files; game appears in 5 files; particle_system appears in 4 files; player appears in 4 files; projectile appears in 4 files
- Evidence: Category K duplicate-name clustering found repeated responsibility names.
- Impact: Potential duplicated logic increases maintenance cost and drift risk.
- Proposed fix: Review clusters, remove accidental duplication, and extract shared helpers where behavior is truly common.
- Acceptance criteria: Documented review of clusters; duplicated implementations are consolidated or justified.
- Expectations: DRY, maintainability, SRP

### Review deep object traversal hotspots
- Severity: medium
- Problem: Deep member-chain hints found in: create_desktop_shortcut.ps1; src/games/Duum/tests/test_bot.py; src/games/Duum/tests/test_entity_manager.py; src/games/Duum/tests/test_particle_system.py; src/games/Duum/tests/test_player.py; src/games/Duum/tests/test_renderer.py; src/games/Force_Field/src/combat_system.py; src/games/Force_Field/src/game_input.py
- Evidence: Category L found repeated chains with three or more member hops.
- Impact: Law of Demeter pressure can make APIs brittle and increase coupling.
- Proposed fix: Review hotspots and introduce boundary methods or DTOs where callers traverse object graphs.
- Acceptance criteria: Hotspots are documented, simplified, or justified; tests cover any API boundary changes.
- Expectations: Law of Demeter, SRP, maintainability

