---
inclusion: always
---

# CI-Matched Local Testing Standards

## 🎯 Core Principle
**NEVER claim tests "pass locally" without running them in a CI-equivalent environment.**

## 📋 Mandatory Pre-Push Checklist

Before pushing ANY code changes, you MUST run these commands in the exact order shown:

### 1. Quality Gate Checks (from repository root)

```bash
# Navigate to repository root
cd /path/to/Games

# Run Ruff with exact CI configuration
ruff check .

# Run Black with exact CI configuration  
black --check .

# Run MyPy (if applicable to changed files)
mypy games/Force_Field/ --config-file games/Force_Field/mypy.ini
```

### 2. Test Execution (matching CI environment)

```bash
# For Force Field tests - MUST match CI exactly
cd games/Force_Field
PYTHONPATH=../.. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest tests/ -v --cov=games.Force_Field --cov-report=xml

# Return to root
cd ../..
```

### 3. Verification Commands

```bash
# Verify no uncommitted formatting changes
git diff --exit-code

# Verify all files are properly formatted
ruff check . && black --check .
```

## 🚫 Prohibited Statements

**NEVER say:**
- ❌ "All tests pass locally"
- ❌ "Ruff/Black checks pass"
- ❌ "Everything looks good locally"

**INSTEAD say:**
- ✅ "Ran CI-equivalent checks: [list specific commands and results]"
- ✅ "Verified with exact CI configuration: [show output]"
- ✅ "Tested in CI-matched environment with PYTHONPATH=../.. and headless pygame"

## 🔧 Tool Version Verification

Before ANY testing session, verify tool versions match CI:

```bash
# Check versions
ruff --version    # Must be: 0.14.10
black --version   # Must be: 25.12.0
python --version  # Prefer: 3.11.x (CI uses 3.11)

# If versions don't match, note the discrepancy in your response
```

## 📁 Working Directory Rules

1. **Ruff/Black**: Always run from repository root (`Games/`)
2. **Pytest**: Run from `games/Force_Field/` with `PYTHONPATH=../..`
3. **MyPy**: Run from repository root with config file path

## 🌍 Environment Variables (Critical!)

Always set these for Force Field tests:
```bash
PYTHONPATH=../..           # Points to repo root for imports
SDL_VIDEODRIVER=dummy      # Headless pygame video
SDL_AUDIODRIVER=dummy      # Headless pygame audio
```

## 🐛 When CI Fails But Local "Passes"

If CI fails but you claimed local success:

1. **Acknowledge the discrepancy immediately**
2. **Re-run with exact CI commands** (shown above)
3. **Identify the difference** (Python version, env vars, working directory, etc.)
4. **Fix the issue** based on CI output, not local results
5. **Document what was different** for future reference

## 📝 Response Template

When reporting test results, use this format:

```
## CI-Equivalent Test Results

**Environment:**
- Python: [version]
- Ruff: [version]  
- Black: [version]
- Working Directory: [path]
- PYTHONPATH: [value]

**Commands Run:**
1. `ruff check .` → [result]
2. `black --check .` → [result]
3. `cd games/Force_Field && PYTHONPATH=../.. pytest tests/` → [result]

**Discrepancies from CI:**
- [List any version or environment differences]

**Confidence Level:** [High/Medium/Low] that CI will pass
```

## 🎓 Learning from Failures

Every time CI fails after claiming local success:
1. Add the specific failure case to this document
2. Update the checklist to catch it next time
3. Improve the testing commands to match CI more closely

## 🔄 CI Configuration Reference

Current CI configuration (from `.github/workflows/ci-standard.yml`):
- **Python Version**: 3.11
- **Ruff Version**: 0.14.10
- **Black Version**: 25.12.0
- **MyPy Version**: 1.13.0
- **Test Working Directory**: `games/Force_Field/`
- **Test PYTHONPATH**: `../..` (relative to Force_Field)
- **Environment**: Ubuntu latest (Linux)

## ⚠️ Critical Reminders

1. **Windows vs Linux**: Path separators and line endings differ
2. **Python 3.11 vs 3.12**: AST parsing can differ subtly
3. **Autofix/Formatting**: Kiro IDE may auto-format files - always check git diff
4. **Import Sorting**: Ruff's import sorting is strict - run `ruff check --fix` before claiming success
5. **Whitespace**: Black is very strict about whitespace - no trailing spaces, consistent indentation

## 🎯 Success Criteria

Only claim "ready for CI" when:
- ✅ All commands above pass with exit code 0
- ✅ `git diff` shows no uncommitted changes
- ✅ Tool versions match CI (or discrepancies are documented)
- ✅ Tests run in CI-equivalent environment (PYTHONPATH, env vars, working directory)
- ✅ You've documented the exact commands run and their output
