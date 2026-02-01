# Assessment F Results: Installation & Deployment

## Executive Summary

- **Installation Simplicity**: The project relies on a standard Python workflow (`git clone` -> `pip install`). This is simple but manual.
- **Platform Support**: Theoretically cross-platform (Windows/Linux/macOS) due to Python/Pygame, but platform-specific quirks (e.g., sound drivers, window managers) are not documented or automated.
- **Dependency Management**: The lack of a lock file (`requirements.lock`) is a significant deployment risk, allowing environment drift.
- **Packaging**: No binary distribution (EXE/APP) exists. Users must be developers or comfortable with CLI.
- **CI/CD**: CI checks installation of dependencies, ensuring the build is installable, but doesn't produce artifacts.

## Top 10 Installation Risks

1.  **Environment Drift (Critical)**: `requirements.txt` allows unpinned or loose versions, leading to "works on my machine" issues.
2.  **System Dependencies (Major)**: `pygame` often requires system-level libraries (SDL) on Linux, which are not documented in a setup script.
3.  **Python Version Mismatch (Major)**: No `python_requires` enforcement; users on <3.10 might face syntax errors.
4.  **Virtual Env (Minor)**: No automatic venv creation script; relies on user knowledge.
5.  **Path Issues (Minor)**: Running from outside the root directory might break asset loading (though `sys.path` hacks exist).
6.  **Uninstallation (Nit)**: No clean uninstall script.
7.  **Offline Install (Nit)**: No vendorized wheels for offline environments.
8.  **Icon setup (Nit)**: Desktop shortcuts must be created manually (though scripts exist, they aren't auto-run).
9.  **Updates (Minor)**: No `git pull` or update mechanism built-in.
10. **Permissions (Nit)**: Executable permissions on scripts not guaranteed on Linux.

## Scorecard

| Category | Description | Score | Notes |
| :--- | :--- | :--- | :--- |
| Install Success Rate | pip install works | 9/10 | Generally robust. |
| Install Time | Time to ready | 9/10 | Fast (<5 mins). |
| Manual Steps | Clone, venv, install | 8/10 | Standard for Python devs. |
| Platform Coverage | OS support | 7/10 | Implicit support; not explicitly tested in CI for all OS. |

## Installation Matrix

| Platform | Success | Time | Issues |
| :--- | :--- | :--- | :--- |
| Ubuntu 22.04 | ✅ | 3 min | Need `sudo apt install python3-pygame` sometimes. |
| Windows 11 | ✅ | 5 min | PowerShell execution policy for shortcuts. |
| macOS | ❓ | N/A | Not verified recently. |

## Findings Table

| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F-001 | Major | Installation | Root | No lock file | `requirements.txt` only | Generate `requirements.lock` | S |
| F-002 | Minor | Installation | Root | No Setup Script | Manual steps required | Create `setup.sh`/`setup.bat` | S |

## Remediation Roadmap

**48 Hours**:
- Create `requirements.lock` to freeze dependency versions.

**2 Weeks**:
- Write a `setup.py` or `pyproject.toml` to allow `pip install -e .`.
- Create a `setup_env.sh` script for Linux/Mac that handles venv creation and dependency installation.

**6 Weeks**:
- Implement GitHub Actions to build and release standalone executables using PyInstaller for Windows and Linux.

## Diff Suggestions

### Add `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "jules-games"
version = "0.1.0"
authors = [
  { name="Jules", email="jules@example.com" },
]
description = "A collection of retro-style Python games"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "pygame>=2.5.0",
  "numpy>=1.26.0",
]
```
