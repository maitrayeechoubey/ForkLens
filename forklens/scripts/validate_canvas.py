#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_NODE_FIELDS = {"id", "type", "title", "lane", "x", "y", "summary"}
REQUIRED_EDGE_FIELDS = {"source", "target"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    node_ids = set()
    for index, node in enumerate(nodes):
        missing = REQUIRED_NODE_FIELDS - set(node)
        if missing:
            errors.append(f"node[{index}] missing {sorted(missing)}")
        node_id = node.get("id")
        if node_id in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
    for index, edge in enumerate(edges):
        missing = REQUIRED_EDGE_FIELDS - set(edge)
        if missing:
            errors.append(f"edge[{index}] missing {sorted(missing)}")
        if edge.get("source") not in node_ids:
            errors.append(f"edge[{index}] unknown source: {edge.get('source')}")
        if edge.get("target") not in node_ids:
            errors.append(f"edge[{index}] unknown target: {edge.get('target')}")
    if not data.get("objective"):
        errors.append("missing objective")
    if not data.get("metrics"):
        errors.append("missing metrics")
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/demo-datacenter.json")
    errors = validate(path)
    if errors:
        print("Canvas validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Canvas OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
