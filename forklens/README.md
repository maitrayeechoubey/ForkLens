# ForkLens

ForkLens is a forkable evidence canvas for Perplexity-powered research.

The thesis: chat is good at answers, but weak at decisions. Hard research work usually fails at the exact point where the web disagrees, the sources change over time, or the answer depends on a human tradeoff. ForkLens turns that moment into a product primitive: a visible fork.

## What it does

ForkLens takes a high-level objective and renders a replayable decision surface:

- **Objective nodes** state the decision and success criteria.
- **Search nodes** show cheap breadth-first discovery.
- **Source clusters** group documents, citations, and reused evidence.
- **Claim and counterclaim nodes** expose agreement and dissent.
- **Computation nodes** capture deterministic scoring and analysis.
- **Fork nodes** pause when a human decision is needed.
- **Decision nodes** explain the path taken and the branches not taken.
- **Metric nodes** show cost, latency, token, and citation-quality targets.

The MVP is dependency-light on purpose. The viewer is plain HTML/CSS/JS, and the CLI uses Python stdlib only. That keeps the artifact easy to review, fork, and run.

## Quick start

```bash
cd workspace/forklens
PYTHONPATH=src python3 -m forklens.cli demo
PYTHONPATH=src python3 -m forklens.cli serve --graph /data/demo-relocation.json --port 8765
```

Open `http://127.0.0.1:8765/public/index.html?graph=/data/demo-relocation.json`.

The browser demo includes a scenario picker and an editable objective prompt. You can switch between the relocation and data-center demos, or type a custom objective directly into the sidebar. Custom edits update the visible decision surface locally; live API regeneration is the next build step.

## Demo topics

The primary end-customer demo asks:

> Maya is a 31-year-old product manager relocating to the Bay Area for a hybrid AI startup role. She needs to be in SoMa 2 to 3 days per week. Her max rent is $4,200/month. She has a dog, wants walkability, wants access to nature, and does not want a commute that ruins her week. She is comparing Hayes Valley, Mission Dolores, Noe Valley, Rockridge, Berkeley, and San Mateo. Where should Maya live if she wants the best balance of commute, rent, safety, walkability, dog-friendly lifestyle, access to nature, and downside risk?

This topic is relatable and monetizable without polluting the answer. It forces the product to handle objective facts, subjective tradeoffs, local sentiment, visual exploration, and human preference forks.

The infrastructure demo still exists at `/data/demo-datacenter.json`:

> Where should a 2027 AI inference data center be sited if the decision must balance grid capacity, water stress, energy cost, renewable procurement, tax incentives, latency to major markets, permitting risk, community opposition, and climate risk?

That topic is stronger for infra strategy, while Maya's relocation demo is stronger for end-customer empathy.

## Why this is a Perplexity-native artifact

Perplexity's strategic wedge is trustable exploration over the open web. ForkLens pushes that idea into a workspace:

1. **Orchestration over model loyalty:** each graph node records why a route was chosen, not just which model answered.
2. **Objectives over instructions:** the user gives a goal; the system decomposes it into lanes, evidence, conflicts, and forks.
3. **Trust-safe monetization:** sponsored discovery cards can live beside evidence nodes, clearly labeled, without corrupting the answer.
4. **Exploration over conversation:** the user compares regions, claims, dissent, and decision paths visually instead of reading one rigid chat answer.

## Token economics to show in the application

The demo should report these metrics in the README, canvas, and final shared artifact:

| Metric | Why it matters | MVP target |
| --- | --- | --- |
| `cost_per_objective` | Total dollars from objective to artifact | `< $0.75` |
| `time_to_first_canvas_node` | Perceived responsiveness | `< 15s` |
| `time_to_first_conflict_fork` | How fast the product finds the real decision | `< 90s` |
| `deep_research_escalation_rate` | Proof that expensive reasoning is used selectively | `< 15%` |
| `context_compression_ratio` | Retrieved source tokens divided by synthesis tokens | `5x-10x` |
| `broken_citation_rate` | Trust bar for final claims | `0` |
| `human_fork_acceptance_rate` | Whether pause points are useful or annoying | `> 50%` |
| `confidence_gain_per_dollar` | Marginal confidence improvement per API dollar | track per branch |

## API adapters

`src/forklens/perplexity.py` includes thin adapters for:

- Search API for cheap breadth-first discovery.
- Chat Completions with Sonar models for cited synthesis.
- Agent API for agentic orchestration, with OpenAI-compatible Responses support available through Perplexity.
- Contextualized embeddings for document-heavy civic or policy packets.

The browser never needs the API key. Generate or refresh a graph from Python, save JSON, then serve the static canvas.

```bash
export PERPLEXITY_API_KEY=pplx-...
PYTHONPATH=src python3 -m forklens.cli search "AI data center grid interconnection delays Northern Virginia" --max-results 10
PYTHONPATH=src python3 -m forklens.cli sonar "Summarize the strongest arguments against siting a new AI inference data center in Northern Virginia. Return cited risks."
```

## Product pitch

I built ForkLens because the next research interface should not be a longer chat. Perplexity is strongest when it turns the open web into cited, checkable intelligence, but complex decisions still break the chat model. The hard part is not getting an answer. The hard part is seeing where the web agrees, where it disagrees, which sources changed over time, and where a human needs to choose the next branch.

ForkLens is an open-source evidence canvas powered by Perplexity’s API. It takes a high-level objective, decomposes it into research lanes, routes cheap discovery to search and embeddings, escalates hard branches to deeper reasoning, and pauses when the evidence conflicts. The output is a forkable visual artifact: source clusters, claim cards, counterclaims, calculations, confidence shifts, and a final narrative that can be shared or replayed. Every step includes a cost and latency trace, so the project proves not just answer quality, but token economics.

The product bet is that exploration deserves its own interface. Chat is right for objective answers, but weak for subjective, high-stakes discovery where users need to compare paths. A visual canvas creates room for trustworthy monetization too: sponsored discovery cards can live beside the evidence graph, clearly labeled and never injected into the answer. That preserves user trust while creating a native ad surface for browsing-based decisions.

## Next build steps

1. Replace seed claims with live Perplexity refresh commands.
2. Add graph-node structured-output schemas for claim extraction.
3. Add source dedupe and citation health checks.
4. Add local Python scoring notebooks behind computation nodes.
5. Add a `public/demo.html` export that bundles JSON into a single shareable file.
6. Add a discovery shelf prototype for labeled, non-intrusive monetization cards.
