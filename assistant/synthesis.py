"""
Cross-document knowledge synthesis across multiple archived research reports.
"""

import sys
from pathlib import Path

from assistant.archive import save_research, search_research_archive
from assistant.client import query_ollama
from assistant.config import (
    MODEL,
    OLLAMA_URL,
    PREVIEW_LENGTH,
    REQUEST_TIMEOUT,
    RESEARCH_DIR,
    SYNTHESIS_REQUIRED_SECTIONS,
)
from assistant.prompts import SYNTHESIS_SYSTEM_PROMPT
from assistant.validation import validate_report_schema


def synthesize_archive_reports(
    query: str,
    max_reports: int = 5,
    research_dir: Path | None = None,
    model: str = MODEL,
    url: str = OLLAMA_URL,
    timeout: int = REQUEST_TIMEOUT,
) -> tuple[Path, str, list[str]]:
    """Synthesize findings across matching archived research reports.

    Returns (output_path, synthesis_analysis, synthesized_report_names).
    """

    target_dir = research_dir if research_dir is not None else RESEARCH_DIR
    matches = search_research_archive(query, research_dir=target_dir)

    if not matches:
        raise ValueError(
            f"No existing research reports found matching query: '{query}'"
        )

    selected = matches[:max_reports]
    compiled_blocks = []
    synthesized_names = []

    for item in selected:
        report_path = item["path"]
        synthesized_names.append(report_path.name)
        text = report_path.read_text(encoding="utf-8")
        compiled_blocks.append(
            f"=== REPORT: {report_path.name} ===\n{text}\n=== END REPORT ==="
        )

    combined_context = "\n\n".join(compiled_blocks)
    user_prompt = f"""Synthesis Topic: {query}

Reports to Synthesize ({len(selected)} reports):
{combined_context}
"""

    analysis = query_ollama(
        user_prompt,
        model=model,
        url=url,
        timeout=timeout,
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
    )

    missing = validate_report_schema(
        analysis,
        required_sections=SYNTHESIS_REQUIRED_SECTIONS,
    )

    output_path = save_research(
        query,
        analysis,
        model=model,
        research_dir=target_dir,
        missing_sections=missing,
        report_title=f"Research Synthesis: {query}",
        report_type="synthesis",
        extra_meta={"synthesized_reports": synthesized_names},
        filename_prefix="synthesis",
    )

    return output_path, analysis, synthesized_names


def display_synthesis(
    query: str,
    max_reports: int = 5,
    research_dir: Path | None = None,
    model: str = MODEL,
    url: str = OLLAMA_URL,
    timeout: int = REQUEST_TIMEOUT,
) -> int:
    """Run synthesis workflow and print formatted results to console."""

    print("\n====================================")
    print("    AI RESEARCH SYNTHESIS")
    print("====================================")
    print(f"Topic: {query}")
    print(f"Model: {model}")
    print("Execution: Local Ollama")
    print("------------------------------------")

    try:
        print(f"Searching archive for reports matching: '{query}'...")
        output_path, analysis, names = synthesize_archive_reports(
            query,
            max_reports=max_reports,
            research_dir=research_dir,
            model=model,
            url=url,
            timeout=timeout,
        )

        print(f"Synthesized {len(names)} reports:")
        for name in names:
            print(f"  - {name}")

        print("\n====================================")
        print("SYNTHESIS REPORT SAVED")
        print("====================================")
        print(f"\nLocation: {output_path}")

        print("\n--- SYNTHESIS PREVIEW ---\n")
        print(analysis[:PREVIEW_LENGTH])

        if len(analysis) > PREVIEW_LENGTH:
            print("\n[Preview truncated. Read the complete Markdown report.]")

        return 0

    except (ValueError, RuntimeError, OSError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nSynthesis interrupted.")
        return 130
