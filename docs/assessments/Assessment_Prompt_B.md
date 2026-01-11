# Assessment B: Games Repository Hygiene, Security & Quality Review

## Assessment Overview

You are a **principal/staff-level Python engineer** conducting an **adversarial, evidence-based** code hygiene and security review of the Games repository. Your job is to **evaluate linting compliance, repository organization, security posture, and adherence to coding standards** as defined in AGENTS.md.

**Reference Documents**:

- `AGENTS.md` - Coding standards and agent guidelines (MANDATORY)
- `ruff.toml` - Ruff linting configuration
- `mypy.ini` - Type checking configuration
- `.pre-commit-config.yaml` - Pre-commit hooks

---

## Context: Games Repository Quality Standards

### Quality Gates (Must Pass)

| Tool       | Configuration             | Enforcement Level      |
| ---------- | ------------------------- | ---------------------- |
| Ruff       | `ruff.toml`               | Strict                 |
| Black      | Default 88 line-length    | Strict                 |
| Mypy       | `mypy.ini`                | Strict (where enabled) |
| Pre-commit | `.pre-commit-config.yaml` | Per-commit             |

### AGENTS.md Standards (Mandatory Compliance)

**Python Standards:**

1. **No `print()` statements** - Use `logging` module
2. **No wildcard imports** - Explicit imports only
3. **No bare `except:` clauses** - Specific exception types
4. **Type hints required** - All public functions

**JavaScript Standards:**

1. Modern ES6+ syntax
2. `const`/`let` only, never `var`
3. `async/await` over callbacks
4. Strict equality (`===`, `!==`)

---

## Your Output Requirements

Do **not** be polite. Do **not** generalize. Do **not** say "looks good overall."
Every claim must cite **exact files/paths, modules, functions**, or **config keys**.

### Deliverables

#### 1. Executive Summary (1 page max)

- Overall hygiene assessment in 5 bullets
- Top 10 hygiene/security risks (ranked)
- "If CI/CD ran strict enforcement today, what fails first?"

#### 2. Scorecard (0-10)

Score each category. For every score ≤8, list evidence and remediation path.

| Category                | Description                     | Weight |
| ----------------------- | ------------------------------- | ------ |
| Ruff Compliance         | Zero violations across codebase | 2x     |
| Mypy Compliance         | Strict type safety              | 2x     |
| Black Formatting        | Consistent formatting           | 1x     |
| AGENTS.md Compliance    | All standards met               | 2x     |
| Security Posture        | No secrets, safe patterns       | 1.5x   |
| Asset Management        | Clean, organized assets         | 1x     |
| Repository Organization | Intuitive structure             | 1x     |

#### 3. Findings Table

| ID    | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
| ----- | -------- | -------- | -------- | ------- | ---------- | --- | ------ |
| B-001 | ...      | ...      | ...      | ...     | ...        | ... | S/M/L  |

**Severity Definitions:**

- **Blocker**: Security vulnerability or CI/CD-breaking violation
- **Critical**: Pervasive hygiene issue affecting multiple files
- **Major**: Significant deviation from AGENTS.md standards
- **Minor**: Isolated hygiene issue
- **Nit**: Style/consistency improvement

#### 4. Linting Violation Inventory

| File               | Ruff Violations    | Mypy Errors | Black Issues  |
| ------------------ | ------------------ | ----------- | ------------- |
| games/duum/game.py | E501 (2), F401 (1) | 3 errors    | Not formatted |
| ...                | ...                | ...         | ...           |

#### 5. Security Audit

| Check                        | Status | Evidence               |
| ---------------------------- | ------ | ---------------------- |
| No hardcoded secrets         | ✅/❌  | grep results           |
| No eval()/exec() usage       | ✅/❌  | grep results           |
| Safe file I/O                | ✅/❌  | Path traversal check   |
| No pickle without validation | ✅/❌  | grep results           |
| Safe user input handling     | ✅/❌  | Input validation check |

#### 6. Asset Management Audit

| Game        | Assets Organized | Naming Convention | Size Appropriate | Git-tracked |
| ----------- | ---------------- | ----------------- | ---------------- | ----------- |
| Duum        | ✅/❌            | ✅/❌             | ✅/❌            | ✅/❌       |
| Force Field | ✅/❌            | ✅/❌             | ✅/❌            | ✅/❌       |
| ...         | ...              | ...               | ...              | ...         |

#### 7. Refactoring Plan

**48 Hours** - CI/CD blockers:

- (List critical violations)

**2 Weeks** - AGENTS.md compliance:

- (List systematic remediation)

**6 Weeks** - Full hygiene graduation:

- (List long-term improvements)

#### 8. Diff-Style Suggestions

Provide ≥5 concrete hygiene fixes with before/after examples.

---

## Mandatory Checks (Hygiene Specific)

### A. AGENTS.md Violations Hunt

Systematically check for violations:

1. **Print Statements**:

   ```bash
   grep -rn "print(" --include="*.py" | grep -v "test_" | grep -v "#"
   ```

2. **Wildcard Imports**:

   ```bash
   grep -rn "from .* import \*" --include="*.py"
   ```

3. **Bare Except Clauses**:

   ```bash
   grep -rn "except:" --include="*.py"
   ```

4. **JavaScript `var` Usage**:
   ```bash
   grep -rn "\bvar\b" --include="*.js"
   ```

### B. Game-Specific Hygiene

For each game:

1. **TypedDict Usage** - Are game data structures typed?
2. **Constants Extraction** - Magic numbers defined as constants?
3. **Event Handling** - Clean event patterns?
4. **Resource Cleanup** - Are resources properly released?

### C. Asset Hygiene

1. **Asset Size** - Are assets reasonably sized for the game type?
2. **Asset Format** - Are modern, efficient formats used?
3. **Asset Duplication** - Are there duplicate assets?
4. **Gitignore** - Are generated assets in `.gitignore`?

### D. Generated Files Audit

Check for files that shouldn't be committed:

- `*.pyc`, `__pycache__/`
- `.ruff_cache/`, `.mypy_cache/`
- `ruff_output*.txt`, `ruff_errors.txt`
- IDE-specific files

---

## Output Format

```markdown
# Assessment B Results: Hygiene, Security & Quality

## Executive Summary

[5 bullets]

## Top 10 Hygiene Risks

[Numbered list with severity]

## Scorecard

[Table with scores and evidence]

## Linting Violation Inventory

[File-by-file violations]

## Security Audit

[Security check results]

## Asset Management Audit

[Game-by-game asset status]

## AGENTS.md Compliance Report

[Standard-by-standard evaluation]

## Findings Table

[Detailed findings]

## Refactoring Plan

[Phased recommendations]

## Diff Suggestions

[Before/after examples]

## Appendix: Cleanup Candidates

[Files/assets to remove or fix]
```

---

## Evaluation Criteria

1. **Linting Compliance** (30%): Ruff, Mypy, Black pass rates
2. **AGENTS.md Compliance** (25%): Adherence to standards
3. **Asset Management** (20%): Clean, organized assets
4. **Security** (25%): Safe patterns, no vulnerabilities

---

_Assessment B focuses on hygiene and security. See Assessment A for architecture/implementation and Assessment C for documentation/player experience._
