"""Static contracts over the inline Python embedded in GitHub Actions workflows.

Workflow files are never imported, so the repo's runtime lint gates
(``ruff``/``bandit``) never see the Python inside their ``run:`` heredocs.
These tests close that gap for the hygiene rules ``CLAUDE.md`` states as
non-negotiable -- most importantly "No bare except: catch specific
exceptions" -- so a silent-data-loss handler cannot be reintroduced.
"""

from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"

# ``except:`` with no exception type, ignoring trailing comments.
BARE_EXCEPT = re.compile(r"^\s*except\s*:\s*(#.*)?$")


def _workflow_files() -> list[Path]:
    """Return every workflow definition, newest-name-first for stable output."""
    return sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))


def test_no_bare_except_in_any_workflow() -> None:
    """A bare ``except:`` in a workflow converts data loss into a green run."""
    workflows = _workflow_files()
    # Guard against a vacuous pass if the directory is ever moved or renamed.
    assert workflows, f"no workflow files found under {WORKFLOWS_DIR}"

    offenders = [
        f"{path.relative_to(WORKFLOWS_DIR.parents[1])}:{lineno}"
        for path in workflows
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if BARE_EXCEPT.match(line)
    ]
    assert not offenders, "bare `except:` in workflow inline Python: " + ", ".join(
        offenders
    )


def _continues_block(line: str, indent: int) -> bool:
    """Is *line* still part of a block opened at *indent*?

    Nested lines are more-indented; the ``except``/``else``/``finally``
    clauses of the same statement sit back at *indent*.
    """
    if not line.strip():
        return True
    line_indent = len(line) - len(line.lstrip())
    if line_indent > indent:
        return True
    return line_indent == indent and line.lstrip().startswith(
        ("except", "else:", "finally:")
    )


def _extract_try_block(source: str, anchor: str) -> ast.Try:
    """Parse the ``try`` statement that starts on the first line after *anchor*.

    Workflow heredocs interleave shell interpolation with Python, so the block
    as a whole is not parseable. The ``try`` statement itself is, once its
    common leading whitespace is stripped.
    """
    lines = source.splitlines()
    start = next(
        i for i, line in enumerate(lines) if anchor in line and line.strip() == anchor
    )
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = start + 1
    while end < len(lines) and _continues_block(lines[end], indent):
        end += 1

    block = ast.parse(textwrap.dedent("\n".join(lines[start:end])))
    statement = block.body[0]
    assert isinstance(statement, ast.Try), f"expected a try statement, got {statement}"
    return statement


def test_comment_queue_load_distinguishes_missing_from_corrupt() -> None:
    """A missing queue starts empty; a corrupt one must not vanish silently.

    ``FileNotFoundError`` is the intended first-run case. Every other read
    failure -- a truncated file, a permission error, a full disk -- previously
    hit the same handler and overwrote the real backlog with an empty queue.
    """
    workflow = WORKFLOWS_DIR / "PR-Comment-Responder.yml"
    try_stmt = _extract_try_block(workflow.read_text(encoding="utf-8"), "try:")

    handled = {
        ast.unparse(handler.type) for handler in try_stmt.handlers if handler.type
    }
    assert len(handled) == len(try_stmt.handlers), "queue load has a bare `except:`"
    assert "FileNotFoundError" in handled, (
        "the first-run case must be caught on its own, not lumped in with "
        f"corruption; handlers were {sorted(handled)}"
    )

    decode_handlers = [
        handler
        for handler in try_stmt.handlers
        if handler.type and "JSONDecodeError" in ast.unparse(handler.type)
    ]
    assert decode_handlers, (
        "a corrupt queue file must be handled explicitly, not left to crash "
        f"or be swallowed; handlers were {sorted(handled)}"
    )
    reports_loss = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        for handler in decode_handlers
        for node in ast.walk(handler)
    )
    assert reports_loss, (
        "resetting a corrupt queue must emit a visible log line so the lost "
        "backlog is diagnosable from the run output"
    )


def test_comment_responder_runs_are_never_cancelled_mid_write() -> None:
    """The queue writer must stay serialised, not cancel-in-progress.

    Every other workflow sets ``cancel-in-progress: true`` to keep the runner
    queue clear, and ``lint-workflow-files.yml`` enforces that. This one is on
    that lint's exception allowlist: it read-modify-writes a shared queue file,
    so cancelling a run mid-write truncates the very backlog the rest of this
    module protects. The exemption and the setting have to stay in step.
    """
    workflow = WORKFLOWS_DIR / "PR-Comment-Responder.yml"
    body = workflow.read_text(encoding="utf-8")
    assert re.search(r"^\s*cancel-in-progress:\s*false\s*$", body, re.MULTILINE), (
        "PR-Comment-Responder must not cancel runs in progress -- a cancelled "
        "run can leave the queue file truncated"
    )

    lint = (WORKFLOWS_DIR / "lint-workflow-files.yml").read_text(encoding="utf-8")
    assert workflow.name in lint, (
        f"{workflow.name} sets cancel-in-progress: false but is missing from the "
        "exception allowlist in lint-workflow-files.yml, so the lint gate will "
        "fail on any change to it"
    )
