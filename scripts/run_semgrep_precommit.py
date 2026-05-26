"""Cross-platform Semgrep pre-push wrapper.

The upstream Semgrep pre-commit package does not install on Windows. Keep the
hook runnable for Windows contributors while preserving fail-closed Semgrep
behavior on platforms where the CLI is supported.
"""

from __future__ import annotations

import shutil
import subprocess
import sys


def main(argv: list[str]) -> int:
    if sys.platform.startswith("win"):
        print(
            "Semgrep pre-push check skipped on Windows; "
            "Semgrep does not support local Windows installs."
        )
        return 0

    semgrep = shutil.which("semgrep")
    if semgrep is None:
        print(
            "semgrep executable not found; install semgrep or run this hook "
            "on a configured runner.",
            file=sys.stderr,
        )
        return 1

    return subprocess.run(
        [semgrep, "--config", "auto", "--quiet", "--no-autofix", *argv],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
