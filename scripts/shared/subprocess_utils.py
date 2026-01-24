"""Shared subprocess utilities for scripts."""

import subprocess
from typing import Any


def run_command(
    cmd: list[str],
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """
    Run a command with consistent error handling.

    Args:
        cmd: Command and arguments as a list
        capture_output: Whether to capture stdout/stderr
        text: Whether to return output as text
        check: Whether to raise exception on non-zero exit
        **kwargs: Additional arguments to pass to subprocess.run

    Returns:
        CompletedProcess instance with command results
    """
    return subprocess.run(
        cmd, capture_output=capture_output, text=text, check=check, **kwargs
    )


def run_gh_command(
    args: list[str],
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Run a GitHub CLI command.

    Args:
        args: Arguments to pass to gh command
        capture_output: Whether to capture stdout/stderr
        text: Whether to return output as text
        check: Whether to raise exception on non-zero exit

    Returns:
        CompletedProcess instance with command results
    """
    return run_command(["gh"] + args, capture_output, text, check)


def run_ruff_check(
    path: str = ".",
    statistics: bool = False,
    json_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Run ruff check with common options.

    Args:
        path: Path to check
        statistics: Whether to include statistics
        json_output: Whether to output JSON format

    Returns:
        CompletedProcess instance with command results
    """
    cmd = ["ruff", "check", path]
    if statistics:
        cmd.append("--statistics")
    if json_output:
        cmd.append("--output-format=json")

    return run_command(cmd, capture_output=True, text=True, check=False)


def run_black_check(path: str = ".") -> subprocess.CompletedProcess[str]:
    """
    Run black check.

    Args:
        path: Path to check

    Returns:
        CompletedProcess instance with command results
    """
    return run_command(
        ["black", "--check", "--quiet", path],
        capture_output=True,
        text=True,
        check=False,
    )


def run_powershell(
    command: str,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    Run a PowerShell command.

    Args:
        command: PowerShell command to execute
        capture_output: Whether to capture stdout/stderr
        text: Whether to return output as text

    Returns:
        CompletedProcess instance with command results
    """
    return run_command(
        ["powershell", "-Command", command], capture_output, text, check=False
    )
