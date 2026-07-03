from __future__ import annotations

import json
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
SCENARIOS = {
    "Maya relocation": "/data/demo-relocation.json",
    "AI data-center siting": "/data/demo-datacenter.json",
}


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_graph(path: str) -> dict:
    return json.loads((ROOT / path.lstrip("/")).read_text(encoding="utf-8"))


def apply_objective(graph: dict, objective: str) -> dict:
    graph = json.loads(json.dumps(graph))
    graph["objective"] = objective
    for node in graph.get("nodes", []):
        if node.get("id") == "objective":
            node["summary"] = objective
            tags = set(node.get("tags", []))
            tags.add("streamlit-prompt")
            node["tags"] = sorted(tags)
            break
    graph.setdefault("metrics", {})["streamlit_prompt_mode"] = "server_side_seed_edit"
    graph["metrics"]["streamlit_prompt_note"] = (
        "This demo updates the objective and evidence surface from seeded graph data. "
        "Live Perplexity regeneration is the next build step."
    )
    return graph


def patch_js_for_streamlit(js: str) -> str:
    """Make the static viewer consume embedded graph JSON inside Streamlit."""
    graph_url_old = '''function graphUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("graph") || "/data/demo-relocation.json";
}'''
    graph_url_new = '''function graphUrl() {
  const params = new URLSearchParams(window.location.search);
  return window.FORKLENS_INITIAL_GRAPH || params.get("graph") || "/data/demo-relocation.json";
}'''
    js = js.replace(graph_url_old, graph_url_new)

    load_old = '''async function loadGraph(url = graphUrl()) {
  setLoadStatus(`Loading ${url}…`);
  const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}_=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load graph: ${response.status}`);
  state.graph = await response.json();
  state.currentGraphUrl = url;
  state.selectedId = "objective";
  state.activeLane = "All";
  state.replayIndex = state.graph.nodes.length;
  syncPromptControls();
  renderAll();
  renderDetails(state.graph.nodes.find((node) => node.id === "objective"));
  setLoadStatus(`Loaded ${state.graph.title}`);
}'''
    load_new = '''async function loadGraph(url = graphUrl()) {
  setLoadStatus(`Loading ${url}…`);
  const embeddedGraphs = window.FORKLENS_EMBEDDED_GRAPHS || {};
  const embeddedGraph = embeddedGraphs[url];
  if (embeddedGraph) {
    state.graph = typeof structuredClone === "function" ? structuredClone(embeddedGraph) : JSON.parse(JSON.stringify(embeddedGraph));
  } else {
    const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}_=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Could not load graph: ${response.status}`);
    state.graph = await response.json();
  }
  state.currentGraphUrl = url;
  state.selectedId = "objective";
  state.activeLane = "All";
  state.replayIndex = state.graph.nodes.length;
  syncPromptControls();
  renderAll();
  renderDetails(state.graph.nodes.find((node) => node.id === "objective"));
  setLoadStatus(`Loaded ${state.graph.title}`);
}'''
    js = js.replace(load_old, load_new)
    return js


def build_embedded_html(initial_path: str, graphs: dict[str, dict]) -> str:
    index = read_text("public/index.html")
    css = read_text("public/styles.css")
    js = patch_js_for_streamlit(read_text("public/app.js"))
    boot = f"""
<script>
window.FORKLENS_INITIAL_GRAPH = {json.dumps(initial_path)};
window.FORKLENS_EMBEDDED_GRAPHS = {json.dumps(graphs, ensure_ascii=False)};
</script>
"""
    index = index.replace('<link rel="stylesheet" href="/public/styles.css?v=3" />', f"<style>\n{css}\n</style>")
    index = index.replace('<link rel="stylesheet" href="/public/styles.css" />', f"<style>\n{css}\n</style>")

    replaced_script = False
    for script_tag in (
        '<script src="/public/app.js?v=3"></script>',
        '<script src="/public/app.js"></script>',
    ):
        if script_tag in index:
            index = index.replace(script_tag, f"{boot}<script>\n{js}\n</script>")
            replaced_script = True
            break
    if not replaced_script:
        index = index.replace("</body>", f"{boot}<script>\n{js}\n</script></body>")
    return index


st.set_page_config(page_title="ForkLens Demo", page_icon="🔎", layout="wide")

st.title("ForkLens")
st.caption("A forkable evidence canvas for Perplexity-style decision research")

with st.sidebar:
    st.header("Demo controls")
    scenario_label = st.selectbox("Scenario", list(SCENARIOS), index=0)
    selected_path = SCENARIOS[scenario_label]
    base_graph = read_graph(selected_path)
    objective = st.text_area("Objective prompt", value=base_graph["objective"], height=220)
    st.info(
        "This Streamlit demo keeps the API key server-side. The current version edits seeded graph data; "
        "live Perplexity regeneration is the next step."
    )

all_graphs = {path: read_graph(path) for path in SCENARIOS.values()}
all_graphs[selected_path] = apply_objective(all_graphs[selected_path], objective)
embedded = build_embedded_html(selected_path, all_graphs)

st.markdown(
    f"""
### {escape(all_graphs[selected_path]['title'])}

Use the canvas below to switch scenarios, type an objective, replay the graph, inspect nodes, and export the JSON artifact.
""",
    unsafe_allow_html=True,
)

components.html(embedded, height=920, scrolling=True)

st.markdown(
    """
---
#### Deploy notes

- Deploy this repo on Streamlit Community Cloud with `streamlit_app.py` as the entrypoint.
- Keep `PERPLEXITY_API_KEY` in Streamlit secrets when live regeneration is added.
- Do not put API keys in `public/app.js`; the browser canvas should only consume saved JSON artifacts.
"""
)
