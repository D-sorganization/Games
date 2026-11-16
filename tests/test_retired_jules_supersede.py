"""Retired supersession automation must not remain dispatchable (Games #891)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = [pytest.mark.unit, pytest.mark.headless_safe]

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
RETIRED_NAME = "Jules Supersede Check"
RETIRED_REFERENCE = ".github/workflows/Jules-Supersede-Check.yml"


def _definitions() -> list[tuple[str, dict[str, Any]]]:
    """Read only GitHub-discoverable definitions; never execute their steps."""
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    assert paths, "workflow inventory must not pass vacuously"
    definitions = []
    for path in paths:
        definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        # PyYAML's YAML 1.1 resolver reads GitHub's unquoted `on` as True.
        if True in definition:
            definition["on"] = definition.pop(True)
        definitions.append((path.name, definition))
    return definitions


def test_retired_superseder_has_no_event_entrypoint() -> None:
    """Neither push nor manual dispatch may start the retired closer."""
    offenders = [
        name
        for name, definition in _definitions()
        if definition.get("name") == RETIRED_NAME and definition.get("on")
    ]
    assert not offenders, f"retired closer remains dispatchable: {offenders}"


def test_no_workflow_calls_retired_superseder() -> None:
    """A reusable-workflow caller must not restore the retired entrypoint."""
    callers = [
        f"{name}:{job_name}"
        for name, definition in _definitions()
        for job_name, job in definition.get("jobs", {}).items()
        if RETIRED_REFERENCE in job.get("uses", "")
    ]
    assert not callers, f"retired closer still has callers: {callers}"


def test_primary_ci_still_accepts_push_and_pull_requests() -> None:
    """Retirement preserves the independent primary test workflow."""
    primary = dict(_definitions())["ci-standard.yml"]
    assert {"push", "pull_request"} <= primary["on"].keys()
