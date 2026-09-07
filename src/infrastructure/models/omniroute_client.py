from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class OmniRouteResponse:
    content: str
    model: str
    role: str = "assistant"
    finish_reason: str = "stop"
    raw_response: Dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OmniRouteClient:
    """
    Unified OpenAI-compatible client interfacing directly with the
    OmniRoute model gateway (default: http://localhost:20128/v1).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:20128/v1",
        api_key: str = "omniroute",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def is_healthy(self) -> bool:
        """Check whether the OmniRoute server is reachable."""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Fetch available models from OmniRoute catalog."""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.warning("Failed to list models from OmniRoute: %s", e)
            return []

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> OmniRouteResponse:
        """
        Execute an OpenAI-compatible chat completion request through OmniRoute.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            usage = data.get("usage", {})

            return OmniRouteResponse(
                content=content or "",
                model=data.get("model", model),
                role=message.get("role", "assistant"),
                finish_reason=choice.get("finish_reason", "stop"),
                raw_response=data,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
        except requests.HTTPError as http_err:
            logger.error(
                "OmniRoute HTTP %s error for model '%s': %s",
                response.status_code if response else "Unknown",
                model,
                response.text if response else str(http_err),
            )
            raise
        except Exception as exc:
            logger.error("OmniRoute request failed for model '%s': %s", model, exc)
            raise
