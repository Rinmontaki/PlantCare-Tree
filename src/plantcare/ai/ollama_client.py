
"""Communicate with the local Ollama API."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaClientError(RuntimeError):
    """Represent an error while communicating with Ollama."""


class OllamaClient:
    """Generate explanations using a local Ollama model."""

    def __init__(
        self,
        model: str = "plantcare-llama:latest",
        base_url: str = "http://127.0.0.1:11434",
        timeout: int = 180,
    ) -> None:
        """Configure the local model connection."""
        self._model = model
        self._endpoint = f"{base_url.rstrip('/')}/api/generate"
        self._timeout = timeout

    def generate_explanation(self, prompt: str) -> str:
        """Generate an explanation using the configured model."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 320,
            },
        }

        request = Request(
            url=self._endpoint,
            data=json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self._timeout,
            ) as response:
                response_bytes = response.read()

        except HTTPError as error:
            raise OllamaClientError(
                f"Ollama returned HTTP {error.code}."
            ) from error

        except (URLError, TimeoutError) as error:
            raise OllamaClientError(
                "Cannot connect to the local Ollama service."
            ) from error

        try:
            result = json.loads(
                response_bytes.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OllamaClientError(
                "Ollama returned an invalid JSON response."
            ) from error

        explanation = result.get("response")

        if (
            not isinstance(explanation, str)
            or not explanation.strip()
        ):
            raise OllamaClientError(
                "Ollama returned an empty explanation."
            )

        return explanation.strip()
