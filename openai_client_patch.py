"""OpenAI-compatible LLM client for Groq integration.

Patches into the classified-agent's LLM system so that
`classified-agent run` works with Groq's API endpoint.

Usage:
    from openai_client_patch import patch_classified_agent
    patch_classified_agent()
"""

from __future__ import annotations

import json
import logging
from typing import Any

from classified_agent.core.llm import BaseLLMClient, LLMMessage, ToolCall
from classified_agent.tools.base import ToolSpec

logger = logging.getLogger("classified")


class GroqOpenAIClient(BaseLLMClient):
    """OpenAI-compatible client targeting Groq's API.

    Groq's chat completions API is fully OpenAI-compatible,
    including tool/function calling support.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "httpx is required for the Groq/OpenAI client. "
                "Install it with: pip install httpx"
            ) from exc

        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        max_tokens: int | None = None,
    ) -> LLMMessage:
        """Send a chat completion request via Groq's OpenAI-compatible API."""
        api_messages = self._convert_messages(messages)
        api_tools = self._convert_tools(tools) if tools else None

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": api_messages,
            "max_tokens": max_tokens or 4096,
        }
        if api_tools:
            payload["tools"] = api_tools

        logger.debug(
            "Groq API call — model=%s, messages=%d, tools=%d",
            self._model,
            len(api_messages),
            len(api_tools or []),
        )

        resp = await self._http.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_response(data)

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert internal LLMMessage list to OpenAI API format."""
        api_msgs: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                api_msgs.append({"role": "system", "content": msg.content})

            elif msg.role == "user":
                api_msgs.append({"role": "user", "content": msg.content})

            elif msg.role == "assistant":
                entry: dict[str, Any] = {"role": "assistant"}
                if msg.content:
                    entry["content"] = msg.content
                if msg.tool_calls:
                    entry["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                    if not msg.content:
                        entry["content"] = ""
                api_msgs.append(entry)

            elif msg.role == "tool_result":
                api_msgs.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content,
                })

        return api_msgs

    def _convert_tools(self, tools: list[ToolSpec]) -> list[dict[str, Any]]:
        """Convert internal ToolSpec list to OpenAI tools format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
            for t in tools
        ]

    def _parse_response(self, data: dict[str, Any]) -> LLMMessage:
        """Parse OpenAI-format response into an LLMMessage."""
        choice = data["choices"][0]
        msg = choice["message"]

        text = msg.get("content", "") or ""
        tool_calls: list[ToolCall] = []

        for tc in msg.get("tool_calls", []):
            fn = tc["function"]
            args = fn.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(
                ToolCall(id=tc["id"], name=fn["name"], arguments=args)
            )

        return LLMMessage(role="assistant", content=text, tool_calls=tool_calls)


def patch_classified_agent() -> None:
    """Monkey-patch the classified-agent LLM factory to support Groq.

    After calling this, setting provider='openai' in classified.toml
    will use the GroqOpenAIClient instead of raising NotImplementedError.
    """
    import classified_agent.core.llm as llm_module

    original_factory = llm_module.create_llm_client

    def patched_factory(config, api_key):
        if config.provider == "openai":
            return GroqOpenAIClient(
                api_key=api_key,
                model=config.model,
                base_url=config.base_url or "https://api.groq.com/openai/v1",
            )
        return original_factory(config, api_key)

    llm_module.create_llm_client = patched_factory
    logger.info("Patched classified-agent LLM factory for Groq/OpenAI support.")
