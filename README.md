# AI Research Assistant

A local-first AI research assistant that transforms research questions into structured, critically examined, and persistent Markdown research documents.

## Mission

Build a reliable personal research tool that uses locally hosted AI to investigate questions, organize knowledge, distinguish evidence from speculation, and preserve useful research for future reference.

The goal is not to build another chatbot. The goal is to build a research system that produces durable intellectual assets.

## Core Principles

- **Local-first:** Run inference locally using Ollama.
- **Privacy:** Research questions and generated reports remain on the local machine.
- **Epistemic integrity:** Distinguish facts, inferences, hypotheses, unknowns, and contradictions.
- **Transparency:** Never fabricate citations or imply that unverified claims are established facts.
- **Persistence:** Save research outputs as readable Markdown documents.
- **Simplicity:** Prefer Python's standard library and avoid unnecessary dependencies.
- **Reproducibility:** Maintain version control and testable behavior.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Local inference | Ollama |
| Model | `qwen3-4b-lowmem:latest` |
| API | Ollama HTTP API |
| Output | Markdown |
| Testing | Python `unittest` |
| Version control | Git |

## Architecture

```text
Research Question
       |
       v
Input Validation
       |
       v
Ollama Client
       |
       v
Research Prompt
       |
       v
Local Language Model
       |
       v
Response Validation
       |
       v
Markdown Renderer
       |
       v
Research Archive
```

## Research Output Format

Each research report should contain:

1. Research title
2. Original question
3. Timestamp
4. Executive summary
5. Key findings
6. FACT — claims supported by identified evidence
7. INFERENCE — conclusions derived from available information
8. HYPOTHESIS — plausible but unverified explanations
9. UNKNOWN — unresolved questions or missing information
10. CONTRADICTION — conflicting claims or evidence
11. Alternative explanations
12. Confidence assessment
13. Recommended next investigations

**Important:** Model-generated statements are not automatically verified facts. Without independent supporting sources, claims must remain explicitly unverified.

## Project Structure

```text
AI-Research-Assistant-Day1/
│
├── assistant/               # Modular application core
│   ├── __init__.py          # Unified package interface
│   ├── config.py            # Configuration & constants
│   ├── prompts.py           # Research & synthesis prompts
│   ├── validation.py        # Input & schema validation
│   ├── client.py            # Local Ollama HTTP client
│   ├── archive.py           # Persistence & archive search
│   └── synthesis.py         # Cross-document synthesis engine
│
├── main.py                  # CLI entry point
├── README.md
├── SPEC.md
├── CONTRIBUTING.md
├── .gitattributes
├── .gitignore
│
├── examples/
│   └── sample_source.txt    # Reference grounded documents
│
├── research/
│   └── .gitkeep             # Local research archive
│
└── tests/
    └── test_main.py         # Automated test suite
```

## Requirements

- Windows 10 or 11
- Python 3
- Git
- Ollama installed and running
- `qwen3-4b-lowmem:latest` downloaded locally

## Configuration

Default Ollama endpoint:

```text
http://localhost:11434
```

Default model:

```text
qwen3-4b-lowmem:latest
```

The application will communicate with Ollama's local chat endpoint:

```text
POST /api/chat
```

No external AI API or paid service is required.

## Running the Application

### 1. Interactive Mode
Run without arguments to enter an interactive prompt:
```powershell
python main.py
```

### 2. Direct Query via CLI Flag
Provide the question directly on the command line:
```powershell
python main.py -q "What are the primary mechanisms of solid-state batteries?"
```

### 3. Grounded Research with Source Ingestion
Pass an external text or Markdown file to ground the investigation and cite evidence:
```powershell
python main.py -q "What did the lab observe regarding low-temperature bottlenecks?" -s examples/sample_source.txt
```

### 4. Archive Management & Search
List all saved research reports in chronological order:
```powershell
python main.py --list
```

Search across all archived research reports for a keyword or concept:
```powershell
python main.py --search "solid-state"
# or short flag:
python main.py -k "efficiency"
```

View the complete content of a previously generated research report:
```powershell
python main.py --view <filename-or-path>
```

### 5. Cross-Document Knowledge Synthesis
Reconcile findings, detect cross-document tensions, and combine insights across multiple archived reports:
```powershell
python main.py --synthesize "solid-state"
# or short flag:
python main.py -x "solid-state"
```

### 6. Custom Configuration
Override the default model, endpoint URL, or timeout:
```powershell
python main.py -q "Your research question" -m "qwen3-4b-lowmem:latest" --timeout 180
```

## Testing

Run the automated test suite with Python's standard `unittest`:

```powershell
python -m unittest discover -s tests -v
```

Or with `pytest`:

```powershell
python -m pytest
```

Tests cover:

- Input validation (empty question, length limits)
- Source document ingestion (validation, file bounds, formatting)
- Ollama connectivity and error handling (HTTP errors, timeouts, network failure)
- Epistemic schema validation and missing section warnings
- Markdown generation, frontmatter quoting, and source provenance tracking
- Report persistence and filename collision deduplication
- Command-line interface argument parsing, archive listing, report display, and keyword search
- Multi-document knowledge synthesis and cross-report contradiction reconciliation

## Development Roadmap

### Stage 1 — Working Prototype

- [x] Establish project specification
- [x] Create README
- [x] Implement application entry point
- [x] Connect to local Ollama
- [x] Generate structured research
- [x] Save Markdown reports
- [x] Implement automated tests

### Stage 2 — Research Quality

- [x] Add source ingestion
- [x] Track claim provenance
- [x] Searchable research archive
- [x] Cross-document knowledge retrieval
- [x] Cross-document contradiction detection

### Stage 3 — Persistent Intelligence

- [x] Searchable research archive
- [x] Cross-document knowledge retrieval
- [ ] Persistent research context
- [ ] Knowledge graph
- [x] Research synthesis across documents

### Stage 4 — Intelligent Workflows

- [ ] Multi-step research workflows
- [ ] Automated investigation plans
- [ ] Research task management
- [ ] Human authorization checkpoints
- [ ] Verified research-to-action workflows

## Definition of Success

The initial version is successful when it can:

1. Accept a research question.
2. Connect to the local Ollama model.
3. Generate a structured research analysis.
4. Distinguish epistemic categories.
5. Save a timestamped Markdown report.
6. Handle failures without silently losing data.
7. Pass its automated tests.

## Project Status

**Current phase:** Stage 1 — Working Prototype

**Current milestone:** Project specification and Git baseline established.

**Latest verified commit:** `d525cbd`

**Development constraint:** Local-only execution with zero paid API dependencies.

---

*Build a research system that compounds knowledge rather than merely generating answers.*