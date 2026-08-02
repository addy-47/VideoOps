"""OpenAI-compatible LLM client wrapper for NVIDIA API / OpenAI endpoints."""

import json
import logging
import time
from typing import Any
from openai import OpenAI
from videoops.config import settings

logger = logging.getLogger(__name__)


class StoryLLMClient:
    """Wrapper around OpenAI-compatible API endpoints for structured content generation."""

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.api_key,
            timeout=30.0,
        )
        self.model = settings.LLM_MODEL

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "You are a creative YouTube Shorts producer. Return valid JSON only.",
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Generate structured JSON output from LLM with automatic retries."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Generating content with model '{self.model}' (attempt {attempt}/{max_retries})")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    response_format={"type": "json_object"} if "nvidia" not in settings.LLM_BASE_URL else None,
                )

                if not response or not response.choices:
                    raise RuntimeError("LLM API returned an empty choices list")

                raw_content = response.choices[0].message.content or ""
                return self._parse_json(raw_content)

            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt}/{max_retries}): {e}")
                last_error = e
                time.sleep(2 ** attempt)

        raise RuntimeError(f"Failed to generate structured JSON after {max_retries} attempts: {last_error}")

    def _parse_json(self, raw_text: str) -> dict[str, Any]:
        """Clean markdown formatting and parse JSON using regex extraction."""
        import re

        cleaned = raw_text.strip()

        # 1. Clean markdown code blocks
        if "```" in cleaned:
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # 2. Extract JSON payload between first { or [ and last } or ]
        first_curly = cleaned.find('{')
        first_square = cleaned.find('[')

        valid_indices = [i for i in (first_curly, first_square) if i != -1]
        start_idx = min(valid_indices) if valid_indices else -1

        last_curly = cleaned.rfind('}')
        last_square = cleaned.rfind(']')
        end_idx = max(last_curly, last_square)

        if start_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx : end_idx + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.error(f"Failed to parse LLM JSON response: {cleaned[:200]}...")
            raise ValueError(f"Invalid JSON returned from LLM: {err}") from err
