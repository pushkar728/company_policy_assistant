"""Provider-agnostic LLM clients (Groq and Google Gemini).

Both providers have generous free tiers, so the project runs at zero cost.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Literal, Mapping

from .config import Settings

PROVIDERS = {
    "groq": {"label": "Groq (GPT-OSS 120B)", "env": "GROQ_API_KEY"},
    "gemini": {"label": "Google Gemini 2.5 Flash", "env": "GEMINI_API_KEY"},
}

MAX_OUTPUT_TOKENS = 2048


class LLMError(Exception):
    """Raised for any failure when talking to an LLM provider."""


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


class BaseLLM(ABC):
    provider: str
    model: str

    @abstractmethod
    def complete(self, system: str, messages: list[ChatMessage], temperature: float = 0.1) -> str:
        """Return the full response text."""

    @abstractmethod
    def stream(
        self, system: str, messages: list[ChatMessage], temperature: float = 0.1
    ) -> Iterator[str]:
        """Yield the response incrementally."""


class GroqLLM(BaseLLM):
    provider = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        from groq import Groq

        self.model = model
        self._client = Groq(api_key=api_key)

    @staticmethod
    def _payload(system: str, messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": "system", "content": system}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]

    def complete(self, system: str, messages: list[ChatMessage], temperature: float = 0.1) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=self._payload(system, messages),
                temperature=temperature,
                max_tokens=MAX_OUTPUT_TOKENS,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001 - surface any SDK/network error uniformly
            raise LLMError(f"Groq request failed: {exc}") from exc

    def stream(
        self, system: str, messages: list[ChatMessage], temperature: float = 0.1
    ) -> Iterator[str]:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=self._payload(system, messages),
                temperature=temperature,
                max_tokens=MAX_OUTPUT_TOKENS,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Groq request failed: {exc}") from exc


class GeminiLLM(BaseLLM):
    provider = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self.model = model
        self._client = genai.Client(api_key=api_key)

    @staticmethod
    def _contents(messages: list[ChatMessage]):
        from google.genai import types

        return [
            types.Content(
                role="user" if m.role == "user" else "model",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in messages
        ]

    @staticmethod
    def _config(system: str, temperature: float):
        from google.genai import types

        return types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )

    def complete(self, system: str, messages: list[ChatMessage], temperature: float = 0.1) -> str:
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=self._contents(messages),
                config=self._config(system, temperature),
            )
            return (response.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Gemini request failed: {exc}") from exc

    def stream(
        self, system: str, messages: list[ChatMessage], temperature: float = 0.1
    ) -> Iterator[str]:
        try:
            for chunk in self._client.models.generate_content_stream(
                model=self.model,
                contents=self._contents(messages),
                config=self._config(system, temperature),
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Gemini request failed: {exc}") from exc


def provider_key(provider: str, env: Mapping[str, str] | None = None) -> str | None:
    """Return the API key configured for ``provider``, if any."""
    env = os.environ if env is None else env
    return (env.get(PROVIDERS[provider]["env"]) or "").strip() or None


def available_providers(env: Mapping[str, str] | None = None) -> list[str]:
    """Providers that already have an API key configured in the environment."""
    return [p for p in PROVIDERS if provider_key(p, env)]


def create_llm(provider: str, api_key: str, settings: Settings) -> BaseLLM:
    """Build an LLM client for ``provider``."""
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown provider '{provider}'. Choose one of: {', '.join(PROVIDERS)}.")
    if not api_key or not api_key.strip():
        raise LLMError(f"No API key supplied for {PROVIDERS[provider]['label']}.")
    if provider == "groq":
        return GroqLLM(api_key.strip(), settings.groq_model)
    return GeminiLLM(api_key.strip(), settings.gemini_model)
