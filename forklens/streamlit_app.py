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
    graph["metrics"]["streamlit_prompt_note"] = "This demo updates the objective and evidence surface from seeded graph data. Live Perplexity regeneration is the next build step."
    return graph


def build_embedded_html(initial_path: str, graphs: dict[str, dict]) -> str:
    index = read_text("public/index.html")
    css = read_text("public/styles.css")
    js = read_text("public/app.js")
    boot = f"""
<script>
window.FORKLENS_INITIAL_GRAPH = {json.dumps(initial_path)};
window.FORKLENS_EMBEDDED_GRAPHS = {json.dumps(graphs, ensure_ascii=False)};
</script>
"""
    index = index.replace('<link rel="stylesheet" href="/public/styles.css?v=3" />', f"<style>\n{css}\n</style>")
    index = index.replace('<script src="/public/app.js?v=3"></script>', f"{boot}<script>\n{js}\n</script>")
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
    st.info("This Streamlit demo keeps the API key server-side. The current version edits seeded graph data; live Perplexity regeneration is the next step.")

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
