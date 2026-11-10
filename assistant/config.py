"""
Configuration and constants for AI Research Assistant.
"""

from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DIR = PROJECT_DIR / "research"

# Ollama Endpoint Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3-4b-lowmem:latest"

# Limits & Timeouts
REQUEST_TIMEOUT = 180
MAX_QUESTION_LENGTH = 5000
MAX_SOURCE_LENGTH = 100000
PREVIEW_LENGTH = 1500

# Required Epistemic Schema Sections
REQUIRED_SECTIONS = [
    "Executive Summary",
    "Key Findings",
    "FACT",
    "INFERENCE",
    "HYPOTHESIS",
    "UNKNOWN",
    "CONTRADICTION",
]

# Required Schema Sections for Cross-Document Synthesis
SYNTHESIS_REQUIRED_SECTIONS = [
    "Synthesis Executive Summary",
    "Corroborated Findings",
    "Cross-Document Contradictions & Tensions",
    "Integrated Knowledge & Inferences",
    "Unified Unknowns & Blindspots",
    "Strategic Next Investigations",
]
