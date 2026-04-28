from __future__ import annotations

from .runtime_llm import AIService as RuntimeLLMService


class AIService(RuntimeLLMService):
    """Coordinator runtime: delega al runtime LLM puro."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
