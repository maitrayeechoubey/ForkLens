from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

NodeType = Literal[
    "objective",
    "search_batch",
    "source_cluster",
    "claim",
    "counterclaim",
    "computation",
    "fork",
    "decision",
    "metric",
]


@dataclass
class Source:
    title: str
    url: str
    date: str | None = None
    last_updated: str | None = None
    snippet: str | None = None
    source: str = "web"


@dataclass
class CostTrace:
    route: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    total_cost_usd: float = 0.0
    latency_ms: int | None = None
    notes: str | None = None


@dataclass
class Node:
    id: str
    type: NodeType
    title: str
    lane: str
    x: int
    y: int
    summary: str
    status: Literal["queued", "running", "blocked", "complete", "needs_human"] = "complete"
    confidence: float | None = None
    tags: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    cost: CostTrace | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    label: str | None = None
    kind: Literal["supports", "contradicts", "routes", "forks", "resolves"] = "routes"


@dataclass
class Canvas:
    id: str
    title: str
    objective: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "0.1"
    lanes: list[str] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    readme: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
