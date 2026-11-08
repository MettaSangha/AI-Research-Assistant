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
├── main.py
├── README.md
├── SPEC.md
├── .gitignore
│
├── research/
│   └── Generated research reports
│
└── tests/
    └── Automated tests
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

*Implementation pending.*

The intended interface:

```powershell
python main.py
```

The application will prompt for a research question, generate a structured analysis using the local model, and save the resulting Markdown document in `research/`.

## Testing

Run the automated test suite:

```powershell
python -m unittest discover -s tests -v
```

Tests should cover:

- Input validation
- Ollama connectivity
- Response parsing
- Error handling
- Markdown generation
- Research file persistence

## Development Roadmap

### Stage 1 — Working Prototype

- [ ] Establish project specification
- [ ] Create README
- [ ] Implement application entry point
- [ ] Connect to local Ollama
- [ ] Generate structured research
- [ ] Save Markdown reports
- [ ] Implement automated tests

### Stage 2 — Research Quality

- [ ] Improve research prompting
- [ ] Add source ingestion
- [ ] Track claim provenance
- [ ] Support evidence verification
- [ ] Improve contradiction detection

### Stage 3 — Persistent Intelligence

- [ ] Searchable research archive
- [ ] Cross-document knowledge retrieval
- [ ] Persistent research context
- [ ] Knowledge graph
- [ ] Research synthesis across documents

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