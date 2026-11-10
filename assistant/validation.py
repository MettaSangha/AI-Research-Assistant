"""
Input validation, filename sanitization, source document loading, and schema verification.
"""

import re
from pathlib import Path

from assistant.config import (
    MAX_QUESTION_LENGTH,
    MAX_SOURCE_LENGTH,
    REQUIRED_SECTIONS,
)


def get_research_question(raw_question: str | None = None) -> str:
    """Collect and validate the user's research question."""

    if raw_question is not None:
        question = raw_question.strip()
    else:
        question = input("\nEnter your research question:\n> ").strip()

    if not question:
        raise ValueError("Research question cannot be empty.")

    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(
            f"Research question exceeds {MAX_QUESTION_LENGTH:,} characters."
        )

    return question


def load_source_document(source_path: str | Path) -> tuple[str, str]:
    """Load and validate an external reference document.

    Returns (filename, text_content).
    """

    path = Path(source_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Source document not found: {source_path}")

    if not path.is_file():
        raise ValueError(f"Source path is not a file: {source_path}")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    content = content.strip()

    if not content:
        raise ValueError(f"Source document is empty: {source_path}")

    if len(content) > MAX_SOURCE_LENGTH:
        raise ValueError(
            f"Source document exceeds {MAX_SOURCE_LENGTH:,} characters (size: {len(content):,} chars)."
        )

    return path.name, content


def sanitize_filename(title: str) -> str:
    """Convert a title into a safe filename."""

    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    filename = re.sub(r"\s+", "-", filename.strip())
    filename = filename.strip(".-")

    return filename[:70] or "research-report"


def validate_report_schema(
    analysis: str,
    required_sections: list[str] | None = None,
) -> list[str]:
    """Check that the generated analysis includes the required epistemic sections.

    Returns a list of missing section titles (empty if fully compliant).
    """

    sections = required_sections if required_sections is not None else REQUIRED_SECTIONS
    missing = []
    for section in sections:
        pattern = rf"(?:^|\n)#+\s+{re.escape(section)}"
        if not re.search(pattern, analysis, re.IGNORECASE):
            missing.append(section)

    return missing
