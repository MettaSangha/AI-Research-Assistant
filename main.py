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
PREVIEW_LENGTH = 1500


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


# ---------------------------------------------------------
# OLLAMA CLIENT
# ---------------------------------------------------------

def query_ollama(
    question: str,
    model: str = MODEL,
    url: str = OLLAMA_URL,
    timeout: int = REQUEST_TIMEOUT,
) -> str:
    """Send a research question to the local Ollama model."""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
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
) -> str:
    """Create a timestamped Markdown research document."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    return f"""---
title: Research Report
created: "{timestamp}"
model: "{model}"
status: AI-generated; claims not independently verified
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
- No independent source verification was performed by this application.
- Treat factual claims as unverified until supported by reliable evidence.
"""


# ---------------------------------------------------------
# FILE PERSISTENCE & ARCHIVE
# ---------------------------------------------------------

def save_research(
    question: str,
    analysis: str,
    model: str = MODEL,
    research_dir: Path | None = None,
) -> Path:
    """Save the research report to the local research archive."""

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{sanitize_filename(question[:60])}.md"

    output_path = target_dir / filename
    markdown = create_markdown(question, analysis, model=model)

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

    print("\n====================================")
    print("       AI RESEARCH ASSISTANT")
    print("====================================")
    print(f"Model: {args.model}")
    print("Execution: Local Ollama")
    print("------------------------------------")

    try:
        if args.question is not None:
            question = get_research_question(args.question)
        else:
            question = get_research_question()

        print("\nInvestigating research question...")
        if (
            args.model == MODEL
            and args.url == OLLAMA_URL
            and args.timeout == REQUEST_TIMEOUT
        ):
            analysis = query_ollama(question)
        else:
            analysis = query_ollama(
                question,
                model=args.model,
                url=args.url,
                timeout=args.timeout,
            )

        print("\nResearch completed.")
        print("\nSaving report...")

        if args.model == MODEL:
            output_path = save_research(question, analysis)
        else:
            output_path = save_research(
                question, analysis, model=args.model
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
