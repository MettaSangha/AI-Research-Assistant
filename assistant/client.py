"""
Ollama HTTP client and network error handling.
"""

import json
import urllib.error
import urllib.request

from assistant.config import MODEL, OLLAMA_URL, REQUEST_TIMEOUT
from assistant.prompts import SYSTEM_PROMPT, format_user_prompt


def query_ollama(
    question: str,
    model: str = MODEL,
    url: str = OLLAMA_URL,
    timeout: int = REQUEST_TIMEOUT,
    source_content: str | None = None,
    source_name: str | None = None,
    system_prompt: str = SYSTEM_PROMPT,
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
                "content": system_prompt,
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
