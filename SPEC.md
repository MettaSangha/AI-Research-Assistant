# AI Research Assistant
**Specification:** v1.0  
**Status:** PROPOSED  
**Date:** 2026-11-08  
**Execution:** Local-only

## 1. Mission

Build a local AI research assistant that transforms questions into structured, critically examined, persistent research documents.

The application should improve the quality of thinking, preserve knowledge, distinguish evidence from speculation, and make research reusable.

## 2. Core objective

Given a research question, the application must:

1. Accept and validate the question.
2. Submit it to a locally hosted language model.
3. Generate a structured research analysis.
4. Classify claims by epistemic status.
5. Identify uncertainty, contradictions, and missing information.
6. Generate a Markdown research document.
7. Save the document locally with a timestamp.

## 3. Technology constraints

- Language: Python.
- Inference server: Ollama.
- Model: `qwen3-4b-lowmem:latest`.
- Endpoint: `http://localhost:11434/api/chat`.
- Output: Markdown.
- Storage: Local filesystem.
- External API dependencies: None.
- Operating costs: $0.
- Version control: Git.

Use Python's standard library wherever practical.

## 4. Application architecture

Question Input  
↓  
Input Validation  
↓  
Ollama Client  
↓  
Research Prompt  
↓  
Model Response  
↓  
Structured Output Validation  
↓  
Markdown Renderer  
↓  
Local Research Archive

Keep model communication, prompt construction, validation, and document generation logically separate.

## 5. Research document schema

Every generated report must contain:

1. Title
2. Original research question
3. Timestamp
4. Executive summary
5. Key findings
6. FACT — established or directly supported claims
7. INFERENCE — conclusions derived from available information
8. HYPOTHESIS — plausible but unverified propositions
9. UNKNOWN — unresolved questions
10. CONTRADICTION — conflicting claims or evidence
11. Alternative explanations
12. Confidence assessment
13. Recommended next investigations

## 6. Epistemic integrity

The application must:

- Never present speculation as verified fact.
- Distinguish model-generated knowledge from externally supported evidence.
- Never fabricate citations or sources.
- Identify missing evidence.
- Acknowledge uncertainty.
- Preserve the original research question.
- Avoid false confidence.

A model response is not independent verification.

## 7. Functional requirements

### FR-01: Question input
Accept a non-empty research question through the command line.

### FR-02: Local inference
Send the question to the configured Ollama model.

### FR-03: Structured analysis
Request the complete research document schema.

### FR-04: Error handling
Handle:
- Ollama unavailable.
- Model unavailable.
- Request timeout.
- Invalid response.
- Empty input.
- File-writing errors.

### FR-05: Persistent output
Save completed research documents under `research/`.

### FR-06: Reproducibility
Document setup, execution, configuration, and known limitations.

## 8. Non-functional requirements

- Local-first execution.
- Minimal dependencies.
- Readable, maintainable code.
- Explicit error handling.
- No silent data loss.
- No automatic modification of existing knowledge repositories.
- No autonomous external actions.

## 9. Day 1 acceptance criteria

The first version is complete when:

- [ ] Python application launches.
- [ ] Ollama connection succeeds.
- [ ] Configured model responds.
- [ ] Research question is accepted.
- [ ] Structured output is generated.
- [ ] Markdown file is saved.
- [ ] Three test questions are executed.
- [ ] Failure handling is tested.
- [ ] README documents execution.
- [ ] Git repository contains the verified initial version.

## 10. Future development

**Phase 2:** Source ingestion and evidence extraction.

**Phase 3:** Searchable knowledge archive.

**Phase 4:** Source provenance and claim verification.

**Phase 5:** Persistent research memory.

**Phase 6:** Multi-step research workflows and agent orchestration.

## 11. Definition of success

The application must reliably transform a research question into a structured, saved, transparent research artifact.

The objective is not to build another chatbot.

The objective is to build reusable research infrastructure.