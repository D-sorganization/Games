# Agent Instructions

## CRITICAL: Do NOT modify workflow runner configuration

Workflow files in `.github/workflows/` that contain `runs-on:` lines must ONLY
use self-hosted runner labels (`d-sorg-fleet`, `d-sorg-fleet-16core`).

**Never change `runs-on:` to `ubuntu-latest`, `windows-latest`, or `macos-latest`.**
This directly causes real financial charges to the organization.

If CI is failing due to missing dependencies, fix the dependency installation
on the self-hosted runner — do NOT switch to a hosted runner as a workaround.

The `.github/CODEOWNERS` file requires `@dieterolson` review for all workflow changes.
Do not attempt to bypass or modify CODEOWNERS.
