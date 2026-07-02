# ForkLens Architecture

## Runtime shape

```text
Objective
  -> planner
  -> cheap Search API breadth pass
  -> source clustering / embeddings
  -> Sonar synthesis for claims
  -> adversarial search for dissent
  -> local sandbox computations
  -> human fork
  -> replayable canvas JSON
  -> static visual artifact
```

## Graph schema

A ForkLens artifact is JSON with:

- `lanes`: visual swimlanes.
- `nodes`: typed evidence objects with position, summary, confidence, sources, cost trace, and details.
- `edges`: relationships such as `supports`, `contradicts`, `forks`, and `resolves`.
- `metrics`: objective-level token, cost, latency, and citation-health metrics.

## Node contract

Each node should answer four questions:

1. What claim or action does this node represent?
2. What sources or computation support it?
3. What route created it, and what did that route cost?
4. What would make the user distrust or fork it?

## Trust contract

Final decision nodes must not cite model-generated URLs. They should cite source objects returned by API calls or uploaded documents. If a source cannot be verified, keep it as a draft source and do not use it in the public artifact.
