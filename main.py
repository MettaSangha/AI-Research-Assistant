#!/usr/bin/env python3
"""
AI Research Assistant

Local-first research assistant powered by Ollama.
Accepts a research question, generates structured analysis,
and saves the result as a Markdown document.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from assistant.config import (
    MAX_QUESTION_LENGTH,
    MAX_SOURCE_LENGTH,
    MODEL,
    OLLAMA_URL,
    PREVIEW_LENGTH,
    PROJECT_DIR,
    REQUEST_TIMEOUT,
    REQUIRED_SECTIONS,
    RESEARCH_DIR,
    SYNTHESIS_REQUIRED_SECTIONS,
)
from assistant.prompts import (
    SYSTEM_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT,
    format_user_prompt,
)
from assistant.validation import (
    get_research_question,
    load_source_document,
    sanitize_filename,
    validate_report_schema,
)
from assistant.client import query_ollama
from assistant.archive import (
    create_markdown,
    display_report,
    display_report_list,
    display_search_results,
    list_research_reports,
    save_research,
    search_research_archive,
)
from assistant.synthesis import (
    display_synthesis,
    synthesize_archive_reports,
)


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
        "-x",
        "--synthesize",
        type=str,
        metavar="QUERY",
        help="Synthesize cross-cutting findings across existing archive reports matching query",
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

    if args.synthesize:
        return display_synthesis(
            args.synthesize,
            model=args.model,
            url=args.url,
            timeout=args.timeout,
        )

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
            print(
                f"Loaded source document: {source_name} ({len(source_content):,} characters)"
            )

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
