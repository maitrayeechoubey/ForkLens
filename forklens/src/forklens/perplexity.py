from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class PerplexityAPIError(RuntimeError):
    pass


@dataclass
class APIResult:
    data: dict[str, Any]
    latency_ms: int

    @property
    def usage(self) -> dict[str, Any]:
        return self.data.get("usage", {}) or {}

    @property
    def total_cost_usd(self) -> float:
        cost = self.usage.get("cost", {}) or {}
        for key in ("total_cost", "request_cost"):
            if key in cost and cost[key] is not None:
                return float(cost[key])
        if "total_cost" in self.usage and self.usage["total_cost"] is not None:
            return float(self.usage["total_cost"])
        return 0.0

    @property
    def input_tokens(self) -> int:
        return int(self.usage.get("input_tokens") or self.usage.get("prompt_tokens") or 0)

    @property
    def output_tokens(self) -> int:
        return int(self.usage.get("output_tokens") or self.usage.get("completion_tokens") or 0)


class PerplexityClient:
    """Small stdlib client for the Perplexity APIs ForkLens uses.

    The client keeps the frontend keyless: call Perplexity from Python/server code,
    then render saved canvas JSON in the browser.
    """

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.perplexity.ai"):
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise PerplexityAPIError("PERPLEXITY_API_KEY is not set")

    def _post(self, path: str, payload: dict[str, Any], timeout: int = 120) -> APIResult:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise PerplexityAPIError(f"Perplexity API HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise PerplexityAPIError(f"Perplexity API connection failed: {error}") from error
        latency_ms = int((time.perf_counter() - started) * 1000)
        return APIResult(data=json.loads(raw), latency_ms=latency_ms)

    def search(self, query: str, max_results: int = 10, **filters: Any) -> APIResult:
        payload = {"query": query, "max_results": max(1, min(max_results, 20))}
        payload.update({key: value for key, value in filters.items() if value is not None})
        return self._post("/search", payload, timeout=60)

    def sonar(
        self,
        prompt: str,
        model: str = "sonar-pro",
        system: str | None = None,
        response_format: dict[str, Any] | None = None,
        web_search_options: dict[str, Any] | None = None,
        max_tokens: int | None = None,
    ) -> APIResult:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if response_format:
            payload["response_format"] = response_format
        if web_search_options:
            payload["web_search_options"] = web_search_options
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return self._post("/v1/sonar", payload, timeout=180)

    def agent(
        self,
        input_text: str,
        preset: str | None = "fast-search",
        model: str | None = None,
        instructions: str | None = None,
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_steps: int | None = None,
        max_output_tokens: int | None = None,
    ) -> APIResult:
        payload: dict[str, Any] = {"input": input_text, "stream": False}
        if preset:
            payload["preset"] = preset
        if model:
            payload["model"] = model
        if instructions:
            payload["instructions"] = instructions
        if response_format:
            payload["response_format"] = response_format
        if tools:
            payload["tools"] = tools
        if max_steps:
            payload["max_steps"] = max_steps
        if max_output_tokens:
            payload["max_output_tokens"] = max_output_tokens
        return self._post("/v1/agent", payload, timeout=180)

    def contextualized_embeddings(
        self,
        documents: list[list[str]],
        model: str = "pplx-embed-context-v1-0.6b",
        dimensions: int | None = 256,
    ) -> APIResult:
        payload: dict[str, Any] = {"input": documents, "model": model}
        if dimensions:
            payload["dimensions"] = dimensions
        return self._post("/v1/contextualizedembeddings", payload, timeout=180)


def message_text(response: dict[str, Any]) -> str:
    if "choices" in response:
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    chunks: list[str] = []
    for item in response.get("output", []) or []:
        for content in item.get("content", []) or []:
            if "text" in content:
                chunks.append(content["text"])
    return "\n".join(chunks)


def normalize_sources(response: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for result in (response.get("search_results", []) or response.get("results", []) or []):
        sources.append({
            "title": result.get("title") or result.get("url") or "Untitled source",
            "url": result.get("url", ""),
            "date": result.get("date"),
            "last_updated": result.get("last_updated"),
            "snippet": result.get("snippet"),
            "source": result.get("source", "web"),
        })
    if not sources:
        for url in response.get("citations", []) or []:
            sources.append({"title": url, "url": url, "source": "citation"})
    for item in response.get("output", []) or []:
        if item.get("type") == "search_results":
            for result in item.get("results", []) or []:
                sources.append({
                    "title": result.get("title") or result.get("url") or "Untitled source",
                    "url": result.get("url", ""),
                    "date": result.get("date"),
                    "last_updated": result.get("last_updated"),
                    "snippet": result.get("snippet"),
                    "source": result.get("source", "web"),
                })
    return sources
