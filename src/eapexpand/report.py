"""
Generation report: collects errors, warnings and notes raised while generating
the USDM artefacts and writes them as Markdown alongside the outputs
(``<output_dir>/<name>_report.md``).

Producers call ``get_report().warning(section, message)`` (or ``error``/``info``);
an entry point calls ``start_report()`` once per run.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

LEVELS = ("error", "warning", "info")
_HEADINGS = {"error": "Errors", "warning": "Warnings", "info": "Notes"}


class GenerationReport:
    def __init__(self) -> None:
        self.started = datetime.now(timezone.utc)
        self.metadata: dict[str, str] = {}
        # level -> section -> messages (insertion ordered, de-duplicated)
        self.entries: dict[str, dict[str, dict[str, None]]] = {level: {} for level in LEVELS}

    def set(self, key: str, value: object) -> None:
        """Record run metadata (inputs, outputs, options)."""
        self.metadata[key] = str(value)

    def add(self, level: str, section: str, message: str) -> None:
        self.entries[level].setdefault(section, {})[str(message)] = None

    def error(self, section: str, message: str) -> None:
        self.add("error", section, message)

    def warning(self, section: str, message: str) -> None:
        self.add("warning", section, message)

    def info(self, section: str, message: str) -> None:
        self.add("info", section, message)

    def count(self, level: str) -> int:
        return sum(len(messages) for messages in self.entries[level].values())

    def to_markdown(self, title: str) -> str:
        lines = [f"# {title} generation report", ""]
        lines.append(f"Generated {self.started.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        lines.append("")
        if self.metadata:
            lines += ["| | |", "|---|---|"]
            lines += [f"| {key} | {value} |" for key, value in self.metadata.items()]
            lines.append("")
        lines += ["## Summary", "", "| Level | Section | Count |", "|---|---|---|"]
        for level in LEVELS:
            for section, messages in self.entries[level].items():
                lines.append(f"| {level} | {section} | {len(messages)} |")
        if not any(self.entries[level] for level in LEVELS):
            lines.append("| | nothing to report | 0 |")
        lines.append("")
        lines.append(
            f"**{self.count('error')} error(s), {self.count('warning')} warning(s), "
            f"{self.count('info')} note(s)**"
        )
        for level in LEVELS:
            if not self.entries[level]:
                continue
            lines += ["", f"## {_HEADINGS[level]}"]
            for section, messages in self.entries[level].items():
                lines += ["", f"### {section} ({len(messages)})", ""]
                lines += [f"- {message}" for message in messages]
        lines.append("")
        return "\n".join(lines)

    def write(self, output_dir: str | Path, name: str) -> Path:
        path = Path(output_dir) / f"{name}_report.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(name))
        return path


_active = GenerationReport()


def start_report() -> GenerationReport:
    """Begin a fresh report for a generation run."""
    global _active
    _active = GenerationReport()
    return _active


def get_report() -> GenerationReport:
    return _active
