"""
TelePort2PI — Ollama Client
Handles all communication with the local Ollama REST API.
"""

import json
import logging
import requests
from typing import Generator, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Lightweight client for the Ollama local AI API.
    Supports both blocking and streaming generation.
    """

    def __init__(self, base_url: str, default_model: str):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
    ) -> str:
        """
        Send a conversation (list of messages) to Ollama and get a response.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            model:    Model name override (uses default_model if None)
            stream:   If True, streams tokens as they arrive (returns full text at end)

        Returns:
            The AI response as a plain string.
        """
        model = model or self.default_model
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        logger.debug("Ollama chat | model=%s | messages=%d", model, len(messages))

        try:
            if stream:
                return self._stream_chat(url, payload)
            else:
                return self._blocking_chat(url, payload)
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Try: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise OllamaTimeoutError("Ollama request timed out. The model may be loading.")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
    ) -> str:
        """
        Simple single-prompt generation (no conversation history).

        Args:
            prompt: The user prompt string
            model:  Model name override
            system: Optional system prompt

        Returns:
            The AI response as a plain string.
        """
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        logger.debug("Ollama generate | model=%s", model)

        try:
            resp = self._session.post(url, json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Try: ollama serve"
            )

    def list_models(self) -> list[str]:
        """
        Return a list of model names currently available in Ollama.
        """
        url = f"{self.base_url}/api/tags"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            return [m["name"] for m in models]
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}."
            )

    def is_available(self) -> bool:
        """Ping Ollama to check if the service is running."""
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def model_exists(self, model_name: str) -> bool:
        """Check if a specific model is available locally."""
        try:
            return model_name in self.list_models()
        except OllamaConnectionError:
            return False

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _blocking_chat(self, url: str, payload: dict) -> str:
        """Send chat request and wait for full response."""
        resp = self._session.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()

    def _stream_chat(self, url: str, payload: dict) -> str:
        """Stream chat response and return the full assembled text."""
        full_response = []
        with self._session.post(url, json=payload, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_response.append(content)
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        return "".join(full_response).strip()


# ------------------------------------------------------------------
# Custom Exceptions
# ------------------------------------------------------------------

class OllamaError(Exception):
    """Base exception for Ollama client errors."""


class OllamaConnectionError(OllamaError):
    """Raised when Ollama service is unreachable."""


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama takes too long to respond."""