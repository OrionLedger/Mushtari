"""
infrastructure/llm/client.py

Thin Groq API wrapper for LLM interactions.
Uses the official `groq` Python library (v1.4.0+) and supports
JSON-structured output for deterministic parsing.
"""

import json
import time
from typing import Optional
from groq import Groq, APIError, APITimeoutError, RateLimitError
from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class GroqClient:
    """
    Lightweight Groq LLM client.

    Reads API key and model from application settings.
    Provides a single `chat()` method with retry logic and
    structured JSON output enforcement.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.llm.api_key or ""
        self.base_url = getattr(settings.llm, "base_url", "https://api.groq.com/openai/v1")
        self.model = settings.llm.model or "llama-3.3-70b-versatile"
        self.temperature = getattr(settings.llm, "temperature", 0.1)
        self.max_retries = 2
        self.timeout = 60

        if not self.api_key:
            logger.warning("No LLM_API_KEY configured — GroqClient will fail at runtime")

        self._client: Optional[Groq] = None

    @property
    def client(self) -> Groq:
        """Lazy-init the Groq client."""
        if self._client is None:
            self._client = Groq(api_key=self.api_key, timeout=self.timeout)
        return self._client

    def chat(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
    ) -> dict:
        """
        Send a chat completion request to Groq with JSON-structured output.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            temperature: Override default temperature (0.0-1.0). Low = deterministic.
            max_tokens: Maximum tokens for the response.

        Returns:
            Parsed JSON dict from the LLM response.

        Raises:
            RuntimeError: If all retries are exhausted or API key is missing.
            ValueError: If the response cannot be parsed as JSON.
        """
        if not self.api_key:
            raise RuntimeError("GroqClient is not configured: LLM_API_KEY is missing")

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start = time.time()
                logger.debug(
                    "Groq LLM call",
                    model=self.model,
                    attempt=attempt + 1,
                    messages=len(messages),
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens,
                    messages=messages,
                    response_format={"type": "json_object"},
                )

                elapsed = (time.time() - start) * 1000
                content = response.choices[0].message.content
                logger.debug("Groq LLM response received", latency_ms=round(elapsed, 1))

                # Parse JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error("LLM returned invalid JSON", error=str(e), content_preview=content[:200])
                    raise ValueError(f"LLM response is not valid JSON: {e}")

            except (APITimeoutError, RateLimitError) as e:
                last_error = e
                logger.warning(
                    "Groq API transient error, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                )
                time.sleep(1.5 ** attempt)  # exponential backoff

            except APIError as e:
                last_error = e
                logger.error("Groq API error", error=str(e), status_code=getattr(e, "status_code", None))
                raise RuntimeError(f"Groq API error: {e}")

            except Exception as e:
                last_error = e
                logger.error("Unexpected Groq error", error=str(e))
                raise RuntimeError(f"Unexpected LLM error: {e}")

        raise RuntimeError(f"LLM call failed after {self.max_retries + 1} retries: {last_error}")


# ── Module-level singleton (lazy) ─────────────────────────────────────────
_client_instance: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create the singleton GroqClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GroqClient()
    return _client_instance
