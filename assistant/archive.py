"""
Report generation, persistence, listing, display, and keyword search.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

from assistant.config import MODEL, REQUIRED_SECTIONS, RESEARCH_DIR
from assistant.validation import sanitize_filename, validate_report_schema


def create_markdown(
    question: str,
    analysis: str,
    model: str = MODEL,
    source_name: str | None = None,
    missing_sections: list[str] | None = None,
    report_title: str = "Research Report",
    report_type: str = "research",
    extra_meta: dict[str, str | list[str]] | None = None,
) -> str:
    """Create a timestamped Markdown research document with YAML frontmatter."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    if missing_sections is None:
        missing_sections = validate_report_schema(analysis)

    source_meta = f'\nsource: "{source_name}"' if source_name else ""
    type_meta = f'\ntype: "{report_type}"' if report_type != "research" else ""

    extra_lines = ""
    if extra_meta:
        for k, v in extra_meta.items():
            if isinstance(v, list):
                items = "\n".join(f'  - "{item}"' for item in v)
                extra_lines += f"\n{k}:\n{items}"
            else:
                extra_lines += f'\n{k}: "{v}"'

    status_line = (
        "AI-generated; grounded in supplied source"
        if source_name
        else (
            "AI-generated; synthesized from archive reports"
            if report_type == "synthesis"
            else "AI-generated; claims not independently verified"
        )
    )

    schema_note = (
        f"- Schema warning: Response omitted expected sections: {', '.join(missing_sections)}.\n"
        if missing_sections
        else "- Schema compliance: All core epistemic sections verified.\n"
    )

    source_provenance = (
        f"- Grounded using provided reference source: `{source_name}`.\n"
        if source_name
        else "- No independent source verification was performed by this application.\n"
    )

    return f"""---
title: "{report_title}"
created: "{timestamp}"
model: "{model}"{source_meta}{type_meta}{extra_lines}
status: {status_line}
---

# {report_title}

## Original Question

{question}

## Research Analysis

{analysis}

---

## Provenance

- Generated locally using Ollama.
- Model: `{model}`.
{source_provenance}{schema_note}- Treat factual claims as unverified until supported by reliable evidence.
"""


def save_research(
    question: str,
    analysis: str,
    model: str = MODEL,
    research_dir: Path | None = None,
    source_name: str | None = None,
    missing_sections: list[str] | None = None,
    report_title: str = "Research Report",
    report_type: str = "research",
    extra_meta: dict[str, str | list[str]] | None = None,
    filename_prefix: str = "",
) -> Path:
    """Save the research report to the local research archive."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_prefix = f"{filename_prefix}-" if filename_prefix else ""
    filename = f"{timestamp}-{base_prefix}{sanitize_filename(question[:60])}.md"

    output_path = target_dir / filename
    markdown = create_markdown(
        question,
        analysis,
        model=model,
        source_name=source_name,
        missing_sections=missing_sections,
        report_title=report_title,
        report_type=report_type,
        extra_meta=extra_meta,
    )

    # Exclusive creation prevents accidental overwrites.
    counter = 1

    while True:
        try:
            with output_path.open("x", encoding="utf-8") as file:
                file.write(markdown)
            break

        except FileExistsError:
            output_path = (
                target_dir
                / f"{timestamp}-{base_prefix}{sanitize_filename(question[:60])}-{counter}.md"
            )
            counter += 1

    return output_path


def list_research_reports(
    research_dir: Path | None = None,
) -> list[Path]:
    """Return all markdown research reports sorted newest to oldest."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    if not target_dir.exists():
        return []

    reports = [p for p in target_dir.glob("*.md") if p.is_file()]
    return sorted(
        reports,
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def display_report_list(
    research_dir: Path | None = None,
) -> int:
    """Print the list of saved research reports."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    reports = list_research_reports(target_dir)

    if not reports:
        print("\nNo research reports found in archive.")
        return 0

    print("\n====================================")
    print("       SAVED RESEARCH ARCHIVE")
    print("====================================")
    for idx, report in enumerate(reports, 1):
        mtime = datetime.fromtimestamp(
            report.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{idx}] {report.name} ({mtime})")
    print("====================================")
    return 0


def display_report(
    target: str,
    research_dir: Path | None = None,
) -> int:
    """Display the full contents of a research report."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    target_path = Path(target)
    if not target_path.exists():
        target_path = target_dir / target

    if not target_path.exists() or not target_path.is_file():
        print(f"\nError: Report not found: {target}", file=sys.stderr)
        return 1

    print(f"\n--- BEGIN REPORT: {target_path.name} ---\n")
    print(target_path.read_text(encoding="utf-8"))
    print(f"\n--- END REPORT: {target_path.name} ---")
    return 0


def search_research_archive(
    keyword: str,
    research_dir: Path | None = None,
) -> list[dict]:
    """Search through all saved research reports for a keyword or phrase."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    if not target_dir.exists() or not keyword.strip():
        return []

    query = keyword.strip().lower()
    matches = []

    for report_path in sorted(target_dir.glob("*.md"), reverse=True):
        if not report_path.is_file():
            continue

        try:
            content = report_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = report_path.read_text(encoding="utf-8", errors="replace")

        lower_content = content.lower()
        if query in lower_content or query in report_path.name.lower():
            matching_sections = []
            for sec in REQUIRED_SECTIONS:
                sec_pattern = rf"#+\s+{re.escape(sec)}[\s\S]*?(?=\n#+|$)"
                match = re.search(sec_pattern, content, re.IGNORECASE)
                if match and query in match.group(0).lower():
                    matching_sections.append(sec)

            snippet = ""
            for line in content.splitlines():
                clean_line = line.strip()
                if (
                    query in clean_line.lower()
                    and not clean_line.startswith("title:")
                    and not clean_line.startswith("created:")
                    and not clean_line.startswith("model:")
                ):
                    snippet = clean_line[:140]
                    break

            matches.append({
                "path": report_path,
                "name": report_path.name,
                "sections": matching_sections,
                "snippet": snippet,
                "mtime": datetime.fromtimestamp(
                    report_path.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            })

    return matches


def display_search_results(
    keyword: str,
    research_dir: Path | None = None,
) -> int:
    """Print search results matching the keyword across archive documents."""

    results = search_research_archive(keyword, research_dir=research_dir)

    print("\n====================================")
    print(f"       SEARCH RESULTS: '{keyword}'")
    print("====================================")

    if not results:
        print(f"No research reports matched '{keyword}'.")
        print("====================================")
        return 0

    print(f"Found {len(results)} matching report(s):\n")
    for idx, r in enumerate(results, 1):
        print(f"[{idx}] {r['name']} ({r['mtime']})")
        if r["sections"]:
            print(f"    Matched Sections: {', '.join(r['sections'])}")
        if r["snippet"]:
            print(f"    Excerpt: \"{r['snippet']}\"")
        print()

    print("====================================")
    return 0
