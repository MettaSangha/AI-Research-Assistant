#!/usr/bin/env python3
"""
AI Research Assistant

Local-first research assistant powered by Ollama.
Accepts a research question, generates structured analysis,
and saves the result as a Markdown document.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3-4b-lowmem:latest"

PROJECT_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = PROJECT_DIR / "research"

REQUEST_TIMEOUT = 180
MAX_QUESTION_LENGTH = 5000
MAX_SOURCE_LENGTH = 100000
PREVIEW_LENGTH = 1500

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Key Findings",
    "FACT",
    "INFERENCE",
    "HYPOTHESIS",
    "UNKNOWN",
    "CONTRADICTION",
]


# ---------------------------------------------------------
# RESEARCH PROMPT
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are a rigorous research analyst.

Examine research questions critically. Distinguish evidence
from speculation and communicate uncertainty honestly.

Return your analysis using these sections:

# Executive Summary

# Key Findings

# FACT
Only include claims supported by evidence explicitly
provided in the conversation or supplied sources.
If no supporting evidence exists, say so.

# INFERENCE
Conclusions reasonably derived from available information.

# HYPOTHESIS
Plausible explanations that remain unverified.

# UNKNOWN
Important unanswered questions and missing information.

# CONTRADICTION
Conflicting claims, evidence, or interpretations.

# Alternative Explanations

# Confidence Assessment

# Next Investigations

Rules:
- Never fabricate citations or sources.
- Never present model-generated claims as verified facts.
- Clearly identify missing evidence.
- Distinguish established knowledge from assumptions.
- Prefer precision over unnecessary verbosity.
- Do not manufacture certainty.
"""


# ---------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------

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


def format_user_prompt(
    question: str,
    source_content: str | None = None,
    source_name: str | None = None,
) -> str:
    """Format the user message with optional grounded source evidence."""

    if not source_content:
        return question

    name_label = source_name or "Supplied Reference Document"

    return f"""Research Question:
{question}

---
REFERENCE DOCUMENT: {name_label}
Evidence from this document must be prioritized for the # FACT section.
Distinguish claims verified by this source from speculation.

{source_content}
--- END REFERENCE DOCUMENT ---
"""


def validate_report_schema(analysis: str) -> list[str]:
    """Check that the generated analysis includes the required epistemic sections.

    Returns a list of missing section titles (empty if fully compliant).
    """

    missing = []
    for section in REQUIRED_SECTIONS:
        pattern = rf"(?:^|\n)#+\s+{re.escape(section)}"
        if not re.search(pattern, analysis, re.IGNORECASE):
            missing.append(section)

    return missing


# ---------------------------------------------------------
# OLLAMA CLIENT
# ---------------------------------------------------------

def query_ollama(
    question: str,
    model: str = MODEL,
    url: str = OLLAMA_URL,
    timeout: int = REQUEST_TIMEOUT,
    source_content: str | None = None,
    source_name: str | None = None,
) -> str:
    """Send a research question to the local Ollama model."""

    user_message = format_user_prompt(
        question,
        source_content=source_content,
        source_name=source_name,
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
        },
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama HTTP error ({exc.code}): {details}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not connect to Ollama: {exc.reason}"
        ) from exc

    except TimeoutError as exc:
        raise RuntimeError(
            "Ollama request timed out."
        ) from exc

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Ollama returned invalid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(
            "Ollama returned an unexpected response format."
        )

    message = result.get("message")

    if not isinstance(message, dict):
        raise RuntimeError(
            "Ollama response is missing a valid message."
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "The model returned an empty response."
        )

    return content.strip()


# ---------------------------------------------------------
# MARKDOWN GENERATION
# ---------------------------------------------------------

def sanitize_filename(title: str) -> str:
    """Convert a title into a safe filename."""

    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    filename = re.sub(r"\s+", "-", filename.strip())
    filename = filename.strip(".-")

    return filename[:70] or "research-report"


def create_markdown(
    question: str,
    analysis: str,
    model: str = MODEL,
    source_name: str | None = None,
    missing_sections: list[str] | None = None,
) -> str:
    """Create a timestamped Markdown research document."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    if missing_sections is None:
        missing_sections = validate_report_schema(analysis)

    source_meta = f'\nsource: "{source_name}"' if source_name else ""
    status_line = (
        "AI-generated; grounded in supplied source"
        if source_name
        else "AI-generated; claims not independently verified"
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
title: Research Report
created: "{timestamp}"
model: "{model}"{source_meta}
status: {status_line}
---

# Research Report

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


# ---------------------------------------------------------
# FILE PERSISTENCE & ARCHIVE
# ---------------------------------------------------------

def save_research(
    question: str,
    analysis: str,
    model: str = MODEL,
    research_dir: Path | None = None,
    source_name: str | None = None,
    missing_sections: list[str] | None = None,
) -> Path:
    """Save the research report to the local research archive."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{sanitize_filename(question[:60])}.md"

    output_path = target_dir / filename
    markdown = create_markdown(
        question,
        analysis,
        model=model,
        source_name=source_name,
        missing_sections=missing_sections,
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
                / f"{timestamp}-{sanitize_filename(question[:60])}-{counter}.md"
            )
            counter += 1

    return output_path


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


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct command-line arguments parser."""

    parser = argparse.ArgumentParser(
        description="AI Research Assistant - Local-first research with Ollama"
    )
    parser.add_argument(
        "-q",
        "--question",
        type=str,
        help="Research question to investigate (non-interactive mode)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=MODEL,
        help=f"Ollama model name (default: {MODEL})",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=OLLAMA_URL,
        help=f"Ollama chat API endpoint (default: {OLLAMA_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=REQUEST_TIMEOUT,
        help=f"Request timeout in seconds (default: {REQUEST_TIMEOUT})",
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        metavar="FILE",
        help="Path to an external text or Markdown source document to ground research",
    )
    parser.add_argument(
        "-k",
        "--search",
        type=str,
        metavar="QUERY",
        help="Search across all saved research reports in archive by keyword",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all saved research reports in archive",
    )
    parser.add_argument(
        "-v",
        "--view",
        type=str,
        metavar="REPORT",
        help="Display the contents of a saved research report by filename or path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the research assistant."""

    parser = build_parser()
    if argv is not None:
        args = parser.parse_args(argv)
    elif len(sys.argv) > 0 and (
        "pytest" in sys.argv[0] or "unittest" in sys.argv[0]
    ):
        args = parser.parse_args([])
    else:
        args = parser.parse_args()

    if args.list:
        return display_report_list()

    if args.view:
        return display_report(args.view)

    if args.search:
        return display_search_results(args.search)

    print("\n====================================")
    print("       AI RESEARCH ASSISTANT")
    print("====================================")
    print(f"Model: {args.model}")
    print("Execution: Local Ollama")
    if args.source:
        print(f"Reference Source: {args.source}")
    print("------------------------------------")

    try:
        source_name = None
        source_content = None

        if args.source:
            source_name, source_content = load_source_document(args.source)
            print(f"Loaded source document: {source_name} ({len(source_content):,} characters)")

        if args.question is not None:
            question = get_research_question(args.question)
        else:
            question = get_research_question()

        print("\nInvestigating research question...")
        if (
            args.model == MODEL
            and args.url == OLLAMA_URL
            and args.timeout == REQUEST_TIMEOUT
            and not source_content
        ):
            analysis = query_ollama(question)
        else:
            analysis = query_ollama(
                question,
                model=args.model,
                url=args.url,
                timeout=args.timeout,
                source_content=source_content,
                source_name=source_name,
            )

        print("\nResearch completed.")

        missing_sections = validate_report_schema(analysis)
        if missing_sections:
            print(
                f"\n[Notice] Response omitted sections: {', '.join(missing_sections)}"
            )

        print("\nSaving report...")

        if args.model == MODEL and not source_name:
            output_path = save_research(question, analysis)
        else:
            output_path = save_research(
                question,
                analysis,
                model=args.model,
                source_name=source_name,
                missing_sections=missing_sections,
            )

        print("\n====================================")
        print("RESEARCH REPORT SAVED")
        print("====================================")
        print(f"\nLocation: {output_path}")

        print("\n--- ANALYSIS PREVIEW ---\n")
        print(analysis[:PREVIEW_LENGTH])

        if len(analysis) > PREVIEW_LENGTH:
            print(
                "\n[Preview truncated. Read the complete Markdown report.]"
            )

        return 0

    except (ValueError, RuntimeError, OSError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nResearch interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
