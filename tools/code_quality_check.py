#!/usr/bin/env python3
"""Quality check script to verify AI-generated code meets standards."""

import sys

from scripts.shared.quality_checks_common import check_file, get_python_files


# ANSI colors for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    if sys.stderr.isatty():
        HEADER = "\033[95m"
        BLUE = "\033[94m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"
        BOLD = "\033[1m"
    else:
        HEADER = ""
        BLUE = ""
        CYAN = ""
        GREEN = ""
        WARNING = ""
        FAIL = ""
        ENDC = ""
        BOLD = ""


def main() -> None:
    """Run quality checks on Python files."""
    file_args = sys.argv[1:] if len(sys.argv) > 1 else None
    python_files = get_python_files(file_args)

    all_issues = []
    for filepath in python_files:
        # Use relaxed checking (no return type hints required)
        issues = check_file(filepath, check_return_hints=False)
        if issues:
            all_issues.append((filepath, issues))

    # Report
    if all_issues:
        msg = f"{Colors.FAIL}{Colors.BOLD}❌ Quality check FAILED{Colors.ENDC}\n\n"
        sys.stderr.write(msg)
        for filepath, issues in all_issues:
            sys.stderr.write(f"\n{Colors.CYAN}{filepath}:{Colors.ENDC}\n")
            for line_num, message, code in issues:
                if line_num > 0:
                    msg = f"  Line {Colors.BOLD}{line_num}{Colors.ENDC}: {message}\n"
                    sys.stderr.write(msg)
                    if code:
                        sys.stderr.write(f"    > {Colors.WARNING}{code}{Colors.ENDC}\n")
                else:
                    sys.stderr.write(f"  {message}\n")

        total_issues = sum(len(issues) for _, issues in all_issues)
        sys.stderr.write(
            f"\n{Colors.FAIL}Total issues: {total_issues}{Colors.ENDC}\n",
        )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
