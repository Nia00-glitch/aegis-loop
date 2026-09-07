from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.infrastructure.models.omniroute_client import OmniRouteClient, OmniRouteResponse

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "model_registry.yaml"


class ModelRouter:
    """
    Central model registry and router for Loop Engineering.
    Dispatches tasks to the appropriate OmniRoute combo / model
    with adaptive fallback across free cloud and local Ollama weights.
    """

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config_path = config_path
        self.config = self._load_config()

        gateway_cfg = self.config.get("gateway", {})
        self.base_url = gateway_cfg.get("base_url", "http://localhost:20128/v1")
        self.api_key = gateway_cfg.get("api_key", "omniroute")
        self.timeout_seconds = gateway_cfg.get("timeout_seconds", 60.0)

        self.client = OmniRouteClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout_seconds=self.timeout_seconds,
        )

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_role_config(self, role: str) -> Dict[str, Any]:
        roles = self.config.get("roles", {})
        if role in roles:
            return roles[role]
        # Default fallback
        return {
            "combo": f"combo/{role}",
            "primary": "kiro/qwen3-coder-next",
            "fallbacks": ["ollama/qwen3:4b-instruct-2507-q4_K_M"],
        }

    def get_model_for_role(self, role: str) -> str:
        """Returns the primary combo identifier for the specified role."""
        role_cfg = self.get_role_config(role)
        return role_cfg.get("combo", f"combo/{role}")

    def execute_with_fallback(
        self,
        role: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> OmniRouteResponse:
        """
        Executes a prompt using adaptive fallback routing:
        1. Attempt the role's configured OmniRoute combo (which itself has priority routing)
        2. If combo encounters upstream failure, attempt primary model directly
        3. Iterate through configured fallback models in order
        """
        role_cfg = self.get_role_config(role)
        candidate_models = [role_cfg.get("combo", f"combo/{role}")]

        primary = role_cfg.get("primary")
        if primary and primary not in candidate_models:
            candidate_models.append(primary)

        for fb in role_cfg.get("fallbacks", []):
            if fb not in candidate_models:
                candidate_models.append(fb)

        last_error = None
        for model in candidate_models:
            try:
                logger.info("Executing role '%s' using model '%s'", role, model)
                response = self.client.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if response and response.content.strip():
                    return response
            except Exception as exc:
                logger.warning(
                    "Model '%s' failed for role '%s' (%s). Advancing to next fallback.",
                    model,
                    role,
                    exc,
                )
                last_error = exc

        raise RuntimeError(
            f"All model candidates exhausted for role '{role}'. Last error: {last_error}"
        )


# Global singleton router instance
router = ModelRouter()
