#!/usr/bin/env python3
"""
Comprehensive Assessment Runner for Categories A-O.
This script performs a detailed audit based on specific prompt requirements.
"""

import ast
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Assessment Topics Map
TOPICS = {
    "A": "Architecture & Implementation",
    "B": "Hygiene, Security & Quality",
    "C": "Documentation & Integration",
    "D": "User Experience & Developer Journey",
    "E": "Performance & Scalability",
    "F": "Installation & Deployment",
    "G": "Testing & Validation",
    "H": "Error Handling & Debugging",
    "I": "Security & Input Validation",
    "J": "Extensibility & Plugin Architecture",
    "K": "Reproducibility & Provenance",
    "L": "Long-Term Maintainability",
    "M": "Educational Resources & Tutorials",
    "N": "Visualization & Export",
    "O": "CI/CD & DevOps",
}


class AssessmentRunner:
    def __init__(self, output_dir: str = "docs/assessments"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Any] = {}
        self.root_dir = Path.cwd()
        self.src_dir = self.root_dir / "src"
        self.games_dir = self.src_dir / "games"

    def run_all(self):
        """Run all assessments A-O."""
        for category_id in TOPICS:
            self.run_assessment(category_id)

        self.generate_completist_report()
        self.generate_comprehensive_report()

    def run_assessment(self, category_id: str):
        """Run a specific assessment."""
        topic = TOPICS.get(category_id, "Unknown")
        logger.info(f"Starting Assessment {category_id}: {topic}")

        # Gather data (simulated or real static analysis)
        data = self._gather_data(category_id)
        self.results[category_id] = data

        # Calculate score
        score = self._calculate_score(category_id, data)
        self.results[category_id]["score"] = score

        # Generate report
        self._generate_report(category_id, topic, data, score)

    def _gather_data(self, category_id: str) -> Dict[str, Any]:
        """Gather evidence for the assessment."""
        if category_id == "A":
            return self._assess_architecture()
        elif category_id == "B":
            return self._assess_hygiene()
        elif category_id == "C":
            return self._assess_documentation()
        elif category_id == "D":
            return self._assess_ux()
        elif category_id == "E":
            return self._assess_performance()
        elif category_id == "F":
            return self._assess_installation()
        elif category_id == "G":
            return self._assess_testing()
        elif category_id == "H":
            return self._assess_error_handling()
        elif category_id == "I":
            return self._assess_security()
        elif category_id == "J":
            return self._assess_extensibility()
        elif category_id == "K":
            return self._assess_reproducibility()
        elif category_id == "L":
            return self._assess_maintainability()
        elif category_id == "M":
            return self._assess_education()
        elif category_id == "N":
            return self._assess_visualization()
        elif category_id == "O":
            return self._assess_cicd()
        else:
            return {"findings": [], "inventory": []}

    def _calculate_score(self, category_id: str, data: Dict[str, Any]) -> int:
        """Calculate score 0-10 based on findings."""
        base_score = 10
        findings = data.get("findings", [])
        for f in findings:
            severity = f.get("severity", "Minor")
            if severity == "Blocker":
                base_score -= 5
            elif severity == "Critical":
                base_score -= 3
            elif severity == "Major":
                base_score -= 1
            elif severity == "Minor":
                base_score -= 0.5
        return max(0, int(base_score))

    def _assess_architecture(self) -> Dict[str, Any]:
        """Assessment A: Architecture."""
        findings = []
        # Check game launcher
        launcher = self.root_dir / "game_launcher.py"
        if not launcher.exists():
            findings.append({"severity": "Critical", "category": "Launcher", "location": "root", "symptom": "game_launcher.py missing", "fix": "Create unified launcher"})

        # Check games dir
        if not self.games_dir.exists():
             findings.append({"severity": "Blocker", "category": "Structure", "location": "src/games", "symptom": "Games directory missing", "fix": "Restore src/games"})
        else:
            # Check individual games structure
            for game in [d for d in self.games_dir.iterdir() if d.is_dir() and d.name not in ["shared", "vendor", "__pycache__", "launcher_assets", "sounds"]]:
                src = game / "src"
                if not src.exists():
                    findings.append({"severity": "Major", "category": "Structure", "location": str(game), "symptom": "Missing src/ directory", "fix": "Move code to src/"})

        return {"findings": findings}

    def _assess_hygiene(self) -> Dict[str, Any]:
        """Assessment B: Hygiene."""
        findings = []

        # Check for print statements
        try:
            grep = subprocess.run(["grep", "-r", "print(", "--include=*.py", "src"], capture_output=True, text=True)
            if grep.stdout:
                count = len(grep.stdout.splitlines())
                findings.append({"severity": "Major", "category": "Code Quality", "location": "Multiple", "symptom": f"Found {count} print() statements", "fix": "Use logging"})
        except Exception:
            pass

        # Check Ruff/Black (simulated check or real if installed)
        # We assume if ruff.toml exists, it's used.
        if not (self.root_dir / "ruff.toml").exists():
             findings.append({"severity": "Major", "category": "Linting", "location": "root", "symptom": "Missing ruff.toml", "fix": "Add ruff configuration"})

        return {"findings": findings}

    def _assess_documentation(self) -> Dict[str, Any]:
        """Assessment C: Documentation."""
        findings = []

        # Check Root README
        if not (self.root_dir / "README.md").exists():
            findings.append({"severity": "Critical", "category": "Docs", "location": "root", "symptom": "Missing README.md", "fix": "Create README"})

        # Check Game READMEs
        if self.games_dir.exists():
             for game in [d for d in self.games_dir.iterdir() if d.is_dir() and d.name not in ["shared", "vendor", "__pycache__", "launcher_assets", "sounds"]]:
                readme = game / "README.md"
                if not readme.exists():
                    findings.append({"severity": "Major", "category": "Docs", "location": str(game), "symptom": "Missing Game README", "fix": f"Add README to {game.name}"})

        return {"findings": findings}

    def _assess_ux(self) -> Dict[str, Any]:
        """Assessment D: UX."""
        findings = []
        # Check if installation instructions exist
        readme = self.root_dir / "README.md"
        if readme.exists():
            content = readme.read_text()
            if "pip install" not in content and "requirements.txt" not in content:
                findings.append({"severity": "Major", "category": "Onboarding", "location": "README.md", "symptom": "No installation instructions found", "fix": "Add Quick Start guide"})

        return {"findings": findings}

    def _assess_performance(self) -> Dict[str, Any]:
        """Assessment E: Performance."""
        findings = []
        # Check for cProfile
        try:
            grep = subprocess.run(["grep", "-r", "cProfile", "--include=*.py", "src"], capture_output=True, text=True)
            if not grep.stdout:
                findings.append({"severity": "Minor", "category": "Profiling", "location": "Codebase", "symptom": "No explicit profiling code found", "fix": "Add profiling hooks for performance critical paths"})
        except Exception:
            pass

        return {"findings": findings}

    def _assess_installation(self) -> Dict[str, Any]:
        """Assessment F: Installation & Deployment."""
        findings = []
        # Check requirements.txt
        if not (self.root_dir / "requirements.txt").exists():
            findings.append({"severity": "Critical", "category": "Dependencies", "location": "root", "symptom": "Missing requirements.txt", "fix": "Create requirements.txt"})

        # Check pyproject.toml
        if not (self.root_dir / "pyproject.toml").exists():
            findings.append({"severity": "Major", "category": "Packaging", "location": "root", "symptom": "Missing pyproject.toml", "fix": "Create pyproject.toml"})

        return {"findings": findings}

    def _assess_testing(self) -> Dict[str, Any]:
        """Assessment G: Testing & Validation."""
        findings = []
        test_dir = self.root_dir / "tests"
        if not test_dir.exists():
             findings.append({"severity": "Critical", "category": "Tests", "location": "root", "symptom": "Missing tests/ directory", "fix": "Create tests directory"})
        else:
            test_files = list(test_dir.glob("test_*.py"))
            if not test_files:
                findings.append({"severity": "Major", "category": "Tests", "location": "tests/", "symptom": "No test files found", "fix": "Add unit tests"})

        return {"findings": findings}

    def _assess_error_handling(self) -> Dict[str, Any]:
        """Assessment H: Error Handling & Debugging."""
        findings = []
        try:
            grep = subprocess.run(["grep", "-r", "except:", "--include=*.py", "src"], capture_output=True, text=True)
            if grep.stdout:
                count = len(grep.stdout.splitlines())
                findings.append({"severity": "Major", "category": "Error Handling", "location": "Multiple", "symptom": f"Found {count} bare except clauses", "fix": "Catch specific exceptions"})
        except Exception:
            pass
        return {"findings": findings}

    def _assess_reproducibility(self) -> Dict[str, Any]:
        """Assessment K: Reproducibility & Provenance."""
        findings = []
        if not (self.root_dir / "poetry.lock").exists() and not (self.root_dir / "package-lock.json").exists():
            findings.append({"severity": "Major", "category": "Dependency Management", "location": "root", "symptom": "No lock file found", "fix": "Commit lock file"})
        return {"findings": findings}

    def _assess_maintainability(self) -> Dict[str, Any]:
        """Assessment L: Long-Term Maintainability."""
        findings = []
        # Check for large files (> 500 lines)
        for p in self.root_dir.glob("**/*.py"):
            if "venv" in p.parts or ".git" in p.parts:
                continue
            try:
                line_count = len(p.read_text().splitlines())
                if line_count > 500:
                    findings.append({"severity": "Major", "category": "Complexity", "location": str(p.relative_to(self.root_dir)), "symptom": f"File too large ({line_count} lines)", "fix": "Split file"})
            except Exception:
                pass
        return {"findings": findings}

    def _assess_education(self) -> Dict[str, Any]:
        """Assessment M: Educational Resources & Tutorials."""
        findings = []
        if not (self.root_dir / "docs" / "tutorials").exists() and not (self.root_dir / "examples").exists():
             findings.append({"severity": "Major", "category": "Onboarding", "location": "docs/", "symptom": "No tutorials or examples found", "fix": "Add examples directory"})
        return {"findings": findings}

    def _assess_visualization(self) -> Dict[str, Any]:
        """Assessment N: Visualization & Export."""
        findings = []
        # Check for visualization libraries
        try:
            grep = subprocess.run(["grep", "-r", "pygame", "--include=*.py", "src"], capture_output=True, text=True)
            if not grep.stdout:
                 findings.append({"severity": "Info", "category": "Tech Stack", "location": "src/", "symptom": "Pygame not explicitly found (check imports)", "fix": "-"})
        except Exception:
            pass
        return {"findings": findings}

    def _assess_cicd(self) -> Dict[str, Any]:
        """Assessment O: CI/CD & DevOps."""
        findings = []
        workflows = self.root_dir / ".github" / "workflows"
        if not workflows.exists():
            findings.append({"severity": "Critical", "category": "CI/CD", "location": ".github/", "symptom": "No workflows directory", "fix": "Create CI pipelines"})
        else:
            if not list(workflows.glob("*.yml")) and not list(workflows.glob("*.yaml")):
                findings.append({"severity": "Major", "category": "CI/CD", "location": ".github/workflows", "symptom": "No workflow files", "fix": "Add CI config"})
        return {"findings": findings}

    def _assess_security(self) -> Dict[str, Any]:
        """Assessment I: Security & Input Validation."""
        findings = []
        try:
            grep = subprocess.run(["grep", "-r", "shell=True", "--include=*.py", "src"], capture_output=True, text=True)
            if grep.stdout:
                findings.append({"severity": "Critical", "category": "Security", "location": "Multiple", "symptom": "subprocess.run(shell=True) detected", "fix": "Set shell=False"})
        except Exception:
            pass

        try:
            grep = subprocess.run(["grep", "-r", "eval(", "--include=*.py", "src"], capture_output=True, text=True)
            if grep.stdout:
                 findings.append({"severity": "Critical", "category": "Security", "location": "Multiple", "symptom": "eval() usage detected", "fix": "Remove eval()"})
        except Exception:
            pass

        return {"findings": findings}

    def _assess_extensibility(self) -> Dict[str, Any]:
        """Assessment J: Extensibility & Plugin Architecture."""
        findings = []
        # Check for ABC imports
        try:
            grep = subprocess.run(["grep", "-r", "from abc import ABC", "--include=*.py", "src"], capture_output=True, text=True)
            if not grep.stdout:
                 findings.append({"severity": "Minor", "category": "Architecture", "location": "Codebase", "symptom": "No Abstract Base Classes detected", "fix": "Define explicit interfaces"})
        except Exception:
            pass
        return {"findings": findings}

    def _generate_report(self, category_id: str, topic: str, data: Dict[str, Any], score: int):
        """Generate the Markdown report."""
        sanitized_topic = topic.replace(' ', '_').replace('&', 'and').replace('/', '_')
        filename = f"Assessment_{category_id}_{sanitized_topic}.md"
        filepath = self.output_dir / filename

        content = f"# Assessment {category_id}: {topic}\n\n"
        content += f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n"
        content += f"**Assessor**: Automated Comprehensive Agent\n\n"

        content += "## Executive Summary\n\n"
        content += "- Automated assessment based on static analysis.\n"
        content += "- Focus on evidence-based findings.\n"
        content += "- Adheres to 'Adversarial' review standard.\n\n"

        content += "## Scorecard\n\n"
        content += f"| Category | Score | Notes |\n| --- | --- | --- |\n| **Overall** | **{score}/10** | Automated Score |\n\n"

        content += "## Findings Table\n\n"
        content += "| ID | Severity | Category | Location | Symptom | Fix |\n"
        content += "| --- | --- | --- | --- | --- | --- |\n"
        if data.get("findings"):
            for i, f in enumerate(data["findings"]):
                content += f"| {category_id}-{i+1:03d} | {f.get('severity', 'Minor')} | {f.get('category', 'General')} | {f.get('location', 'Repo')} | {f.get('symptom', 'Issue')} | {f.get('fix', 'Fix it')} |\n"
        else:
            content += f"| {category_id}-000 | Info | Setup | - | No critical findings detected by automation. | - |\n"

        content += "\n## Refactoring Plan\n\n"
        content += "**48 Hours**\n- Review automated findings.\n\n"
        content += "**2 Weeks**\n- Address High severity issues.\n\n"
        content += "**6 Weeks**\n- Optimize for long-term health.\n"

        with open(filepath, "w") as f:
            f.write(content)

        logger.info(f"Generated report: {filepath}")

    def generate_completist_report(self):
        """Generate the completist report from .jules/completist_data/."""
        completist_dir = self.output_dir / "completist"
        completist_dir.mkdir(parents=True, exist_ok=True)
        data_dir = self.root_dir / ".jules" / "completist_data"

        report_data = {}
        total_issues = 0

        for filename in ["abstract_methods.txt", "incomplete_docs.txt", "not_implemented.txt", "todo_markers.txt"]:
            file_path = data_dir / filename
            if file_path.exists():
                lines = file_path.read_text().splitlines()
                count = len(lines)
                report_data[filename] = {"count": count, "sample": lines[:5]}
                total_issues += count
            else:
                report_data[filename] = {"count": 0, "sample": []}

        score = max(0, 10 - (total_issues // 10)) # Deduct 1 point per 10 issues

        content = f"# Completist Report: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        content += f"**Score**: {score}/10\n\n"
        content += "## Summary\n\n"
        content += f"Total issues found: {total_issues}\n\n"

        for key, val in report_data.items():
            name = key.replace(".txt", "").replace("_", " ").title()
            content += f"### {name}: {val['count']}\n"
            if val["sample"]:
                content += "Sample:\n"
                for line in val["sample"]:
                    content += f"- {line}\n"
            content += "\n"

        output_file = completist_dir / f"Completist_Report_{datetime.now().strftime('%Y-%m-%d')}.md"
        output_file.write_text(content)
        logger.info(f"Generated Completist Report: {output_file}")

        self.results["Completist"] = {"score": score, "total_issues": total_issues}

    def generate_comprehensive_report(self):
        """Generate the final comprehensive assessment."""
        content = f"# Comprehensive Assessment Report\n\n"
        content += f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n"
        content += "**Status**: CRITICAL AUDIT COMPLETE\n\n"

        # Unified Scorecard
        content += "## Unified Scorecard\n\n"
        content += "| Category | Score | Assessment |\n"
        content += "| --- | --- | --- |\n"

        total_score = 0
        count = 0

        # General Categories A-O
        for category_id in sorted(TOPICS.keys()):
            if category_id in self.results:
                score = self.results[category_id].get("score", 0)
                topic = TOPICS[category_id]
                content += f"| {category_id}: {topic} | {score}/10 | {'Pass' if score >= 8 else 'Fail' if score < 5 else 'Warn'} |\n"
                total_score += score
                count += 1

        # Completist
        if "Completist" in self.results:
            score = self.results["Completist"]["score"]
            content += f"| Completist Audit | {score}/10 | {'Pass' if score >= 8 else 'Fail'} |\n"
            total_score += score
            count += 1

        avg_score = total_score / count if count > 0 else 0
        content += f"| **Unified Grade** | **{avg_score:.1f}/10** | **OVERALL** |\n\n"

        # Pragmatic Programmer Review Integration
        content += "## Pragmatic Programmer Review Findings\n\n"
        pragmatic_file = self.output_dir / "pragmatic_programmer" / "review_2026-02-24.md"
        if pragmatic_file.exists():
            content += "### Summary from Pragmatic Review\n\n"
            # Extract findings section or list major items
            try:
                prag_text = pragmatic_file.read_text()
                if "## Findings" in prag_text:
                    findings_section = prag_text.split("## Findings")[1].split("##")[0].strip()
                    # Include first 10 lines of findings
                    preview = "\n".join(findings_section.splitlines()[:20])
                    content += preview + "\n...\n(See full Pragmatic Review for details)\n"
                else:
                    content += "Refer to [Pragmatic Review](pragmatic_programmer/review_2026-02-24.md)\n"
            except Exception:
                content += "Could not read Pragmatic Review file.\n"
        else:
             content += "Pragmatic Review file not found.\n"

        # Top Recommendations
        content += "\n## Top 10 Unified Recommendations\n\n"
        all_findings = []
        for cat, data in self.results.items():
            if cat == "Completist": continue
            for f in data.get("findings", []):
                all_findings.append({**f, "origin": cat})

        # Sort by severity (Blocker > Critical > Major > Minor)
        severity_map = {"Blocker": 0, "Critical": 1, "Major": 2, "Minor": 3, "Info": 4}
        all_findings.sort(key=lambda x: severity_map.get(x.get("severity", "Info"), 5))

        for i, f in enumerate(all_findings[:10]):
             content += f"{i+1}. **[{f['origin']}] {f.get('category')}**: {f.get('symptom')} ({f.get('severity')})\n"
             content += f"   - *Fix*: {f.get('fix')}\n"

        filepath = self.output_dir / "Comprehensive_Assessment.md"
        filepath.write_text(content)
        logger.info(f"Generated Comprehensive Report: {filepath}")

if __name__ == "__main__":
    runner = AssessmentRunner()
    runner.run_all()
