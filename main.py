#!/usr/bin/env python3
"""
AI Research Assistant

Local-first research assistant powered by Ollama.
Accepts a research question, generates structured analysis,
and saves the result as a Markdown document.
"""

from __future__ import annotations

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

def get_research_question() -> str:
    """Collect and validate the user's research question."""

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

def query_ollama(question: str) -> str:
    """Send a research question to the local Ollama model."""

    payload = {
        "model": MODEL,
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
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
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


def create_markdown(question: str, analysis: str) -> str:
    """Create a timestamped Markdown research document."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    return f"""---
title: Research Report
created: "{timestamp}"
model: "{MODEL}"
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
- Model: `{MODEL}`.
- No independent source verification was performed by this application.
- Treat factual claims as unverified until supported by reliable evidence.
"""


# ---------------------------------------------------------
# FILE PERSISTENCE
# ---------------------------------------------------------

def save_research(question: str, analysis: str) -> Path:
    """Save the research report to the local research archive."""

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{sanitize_filename(question[:60])}.md"

    output_path = RESEARCH_DIR / filename
    markdown = create_markdown(question, analysis)

    # Exclusive creation prevents accidental overwrites.
    counter = 1

    while True:
        try:
            with output_path.open("x", encoding="utf-8") as file:
                file.write(markdown)
            break

        except FileExistsError:
            output_path = (
                RESEARCH_DIR
                / f"{timestamp}-{sanitize_filename(question[:60])}-{counter}.md"
            )
            counter += 1

    return output_path


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

def main() -> int:
    """Run the research assistant."""

    print("\n====================================")
    print("       AI RESEARCH ASSISTANT")
    print("====================================")
    print(f"Model: {MODEL}")
    print("Execution: Local Ollama")
    print("------------------------------------")

    try:
        question = get_research_question()

        print("\nInvestigating research question...")
        analysis = query_ollama(question)

        print("\nResearch completed.")
        print("\nSaving report...")

        output_path = save_research(question, analysis)

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
