"""
Lazy import wrappers for the external model runners.

Importing everything eagerly requires heavyweight dependencies (e.g., vllm)
even when we only need the OpenAI runner.  Defer the imports so lightweight
setups can keep the footprint small while still exposing the same public API.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "OpenAIRunner",
    "HFTacticGenerator",
    "VLLMTacticGenerator",
    "ClaudeRunner",
    "GeminiRunner",
]


def _load(name: str) -> Any:
    module_map = {
        "OpenAIRunner": ("external_models.oai_runner", "OpenAIRunner"),
        "HFTacticGenerator": ("external_models.hf_runner", "HFTacticGenerator"),
        "VLLMTacticGenerator": (
            "external_models.vllm_runner",
            "VLLMTacticGenerator",
        ),
        "ClaudeRunner": ("external_models.claude_runner", "ClaudeRunner"),
        "GeminiRunner": ("external_models.gemini_runner", "GeminiRunner"),
    }
    if name not in module_map:
        raise AttributeError(f"module 'external_models' has no attribute '{name}'")
    module_name, attr_name = module_map[name]
    module = import_module(module_name)
    return getattr(module, attr_name)


def __getattr__(name: str) -> Any:
    return _load(name)


def __dir__() -> list[str]:
    return sorted(__all__)
