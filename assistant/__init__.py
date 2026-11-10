"""
AI Research Assistant package.
"""

from assistant.config import (
    MAX_QUESTION_LENGTH,
    MAX_SOURCE_LENGTH,
    MODEL,
    OLLAMA_URL,
    PREVIEW_LENGTH,
    PROJECT_DIR,
    REQUEST_TIMEOUT,
    REQUIRED_SECTIONS,
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

__all__ = [
    "MAX_QUESTION_LENGTH",
    "MAX_SOURCE_LENGTH",
    "MODEL",
    "OLLAMA_URL",
    "PREVIEW_LENGTH",
    "PROJECT_DIR",
    "REQUEST_TIMEOUT",
    "REQUIRED_SECTIONS",
    "SYSTEM_PROMPT",
    "SYNTHESIS_SYSTEM_PROMPT",
    "create_markdown",
    "display_report",
    "display_report_list",
    "display_search_results",
    "display_synthesis",
    "format_user_prompt",
    "get_research_question",
    "list_research_reports",
    "load_source_document",
    "query_ollama",
    "sanitize_filename",
    "save_research",
    "search_research_archive",
    "synthesize_archive_reports",
    "validate_report_schema",
]
