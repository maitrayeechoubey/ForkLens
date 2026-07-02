const svgNS = "http://www.w3.org/2000/svg";
const state = {
  graph: null,
  selectedId: null,
  activeLane: "All",
  replayIndex: Infinity,
  currentGraphUrl: null,
};

const typeLabels = {
  objective: "Objective",
  search_batch: "Search",
  source_cluster: "Sources",
  claim: "Claim",
  counterclaim: "Dissent",
  computation: "Calc",
  fork: "Fork",
  decision: "Decision",
  metric: "Metric",
};

function qs(selector) { return document.querySelector(selector); }
function qsa(selector) { return [...document.querySelectorAll(selector)]; }
function el(name, attrs = {}, text = null) {
  const node = document.createElementNS(svgNS, name);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
  if (text !== null) node.textContent = text;
  return node;
}
function html(name, className, text) {
  const node = document.createElement(name);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function graphUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("graph") || "/data/demo-relocation.json";
}

async function loadGraph(url = graphUrl()) {
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
}

function setLoadStatus(message) {
  const status = qs("#loadStatus");
  if (status) status.textContent = message;
}

function syncPromptControls() {
  const select = qs("#scenarioSelect");
  const input = qs("#objectiveInput");
  if (!select || !input || !state.graph) return;
  const option = [...select.options].find((item) => item.value === state.currentGraphUrl);
  select.value = option ? state.currentGraphUrl : "custom";
  input.value = state.graph.objective || "";
}

function applyObjective() {
  const input = qs("#objectiveInput");
  const objective = input.value.trim();
  if (!objective || !state.graph) return;
  state.graph.objective = objective;
  if (qs("#scenarioSelect").value === "custom") {
    state.graph.title = "ForkLens Demo: Custom Decision Surface";
    state.graph.id = "custom-forklens-objective";
  }
  const objectiveNode = (state.graph.nodes || []).find((node) => node.id === "objective");
  if (objectiveNode) {
    objectiveNode.title = qs("#scenarioSelect").value === "custom" ? "Custom decision objective" : objectiveNode.title;
    objectiveNode.summary = objective;
    objectiveNode.tags = [...new Set([...(objectiveNode.tags || []), "typed-prompt"])];
  }
  state.graph.metrics = {
    ...(state.graph.metrics || {}),
    prompt_edit_mode: "local_canvas_only",
    prompt_edit_note: "This updates the visible decision surface. Live API regeneration is the next build step.",
  };
  state.selectedId = "objective";
  renderAll();
  renderDetails(objectiveNode);
}

function resetScenario() {
  const selected = qs("#scenarioSelect").value;
  loadGraph(selected === "custom" ? graphUrl() : selected).catch(showLoadError);
}

function updateUrl(url) {
  const next = new URL(window.location.href);
  next.searchParams.set("graph", url);
  window.history.replaceState({}, "", next.toString());
}

function visibleNodes() {
  const nodes = state.graph.nodes || [];
  return nodes.filter((node, index) => {
    const laneOk = state.activeLane === "All" || node.lane === state.activeLane;
    const replayOk = index < state.replayIndex;
    return laneOk && replayOk;
  });
}

function visibleNodeIds() {
  return new Set(visibleNodes().map((node) => node.id));
}

function renderAll() {
  qs("#title").textContent = state.graph.title;
  qs("#objective").textContent = state.graph.objective;
  qs("#canvasMeta").textContent = `${state.graph.nodes.length} nodes · ${state.graph.edges.length} edges · ${state.graph.version || "0.1"}`;
  renderMetrics();
  renderLaneFilters();
  renderCanvas();
  const selected = state.graph.nodes.find((node) => node.id === state.selectedId);
  if (selected) renderDetails(selected);
  if (!selected) renderEmptyDetails();
}

function renderMetrics() {
  const metrics = state.graph.metrics || {};
  const container = qs("#metrics");
  container.innerHTML = "";
  const entries = Object.entries(metrics).slice(0, 8);
  for (const [key, value] of entries) {
    const dt = html("dt", null, key.replaceAll("_", " "));
    const dd = html("dd", null, typeof value === "number" ? String(Number(value.toFixed ? value.toFixed(4) : value)) : String(value));
    container.append(dt, dd);
  }
}

function renderLaneFilters() {
  const container = qs("#laneFilters");
  container.innerHTML = "";
  const lanes = ["All", ...(state.graph.lanes || [])];
  lanes.forEach((lane) => {
    const chip = html("button", `chip ${lane === state.activeLane ? "active" : ""}`, lane);
    chip.addEventListener("click", () => {
      state.activeLane = lane;
      renderAll();
    });
    container.appendChild(chip);
  });
}

function renderCanvas() {
  qs("#lanes").innerHTML = "";
  qs("#edges").innerHTML = "";
  qs("#nodes").innerHTML = "";
  renderLaneBands();
  renderEdges();
  renderNodes();
}

function laneYPositions() {
  const map = new Map();
  const nodes = state.graph.nodes || [];
  for (const node of nodes) {
    if (!map.has(node.lane)) map.set(node.lane, []);
    map.get(node.lane).push(node.y);
  }
  return map;
}

function renderLaneBands() {
  const group = qs("#lanes");
  const lanes = state.graph.lanes || [];
  const positions = laneYPositions();
  lanes.forEach((lane) => {
    const ys = positions.get(lane) || [80];
    const y = Math.min(...ys) - 34;
    const height = Math.max(82, Math.max(...ys) - Math.min(...ys) + 116);
    const laneGroup = el("g", { class: "lane-label" });
    laneGroup.appendChild(el("rect", { x: 28, y, width: 2025, height, rx: 18 }));
    laneGroup.appendChild(el("text", { x: 48, y: y + 25 }, lane));
    group.appendChild(laneGroup);
  });
}

function nodeMap() {
  return new Map((state.graph.nodes || []).map((node) => [node.id, node]));
}

function renderEdges() {
  const group = qs("#edges");
  const nodes = nodeMap();
  const visible = visibleNodeIds();
  for (const edge of state.graph.edges || []) {
    if (!visible.has(edge.source) || !visible.has(edge.target)) continue;
    const from = nodes.get(edge.source);
    const to = nodes.get(edge.target);
    if (!from || !to) continue;
    const x1 = from.x + 235;
    const y1 = from.y + 58;
    const x2 = to.x - 10;
    const y2 = to.y + 58;
    const midX = (x1 + x2) / 2;
    const path = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
    group.appendChild(el("path", { class: `edge ${edge.kind || "routes"}`, d: path }));
    if (edge.label) {
      group.appendChild(el("text", { class: "edge-label", x: midX - 34, y: (y1 + y2) / 2 - 6 }, edge.label));
    }
  }
}

function wrapText(text, maxChars, maxLines) {
  const words = String(text || "").split(/\s+/);
  const lines = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (candidate.length > maxChars) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
    if (lines.length === maxLines) break;
  }
  if (line && lines.length < maxLines) lines.push(line);
  if (words.join(" ").length > lines.join(" ").length && lines.length) lines[lines.length - 1] += "…";
  return lines;
}

function renderNodes() {
  const group = qs("#nodes");
  for (const node of visibleNodes()) {
    const g = el("g", { class: `node ${node.type} ${node.id === state.selectedId ? "active" : ""}`, transform: `translate(${node.x}, ${node.y})`, tabindex: 0 });
    g.appendChild(el("rect", { class: "card", x: 0, y: 0, width: 245, height: 116, rx: 18 }));
    g.appendChild(el("rect", { class: "type-pill", x: 14, y: 12, width: 78, height: 22, rx: 11 }));
    g.appendChild(el("text", { class: "pill-text", x: 26, y: 27 }, typeLabels[node.type] || node.type));
    const conf = node.confidence === null || node.confidence === undefined ? "" : `${Math.round(node.confidence * 100)}%`;
    g.appendChild(el("text", { class: "confidence", x: 185, y: 27 }, conf));
    g.appendChild(el("text", { class: "title", x: 14, y: 54 }, node.title.slice(0, 31)));
    wrapText(node.summary, 35, 3).forEach((line, index) => {
      g.appendChild(el("text", { class: "summary", x: 14, y: 76 + index * 16 }, line));
    });
    if (node.status === "needs_human") {
      g.appendChild(el("circle", { cx: 225, cy: 20, r: 6, fill: "#fbbf24" }));
    }
    g.addEventListener("click", () => {
      state.selectedId = node.id;
      renderAll();
      renderDetails(node);
    });
    g.addEventListener("keyup", (event) => {
      if (event.key === "Enter") {
        state.selectedId = node.id;
        renderAll();
        renderDetails(node);
      }
    });
    group.appendChild(g);
  }
}

function renderEmptyDetails() {
  qs("#detailTitle").textContent = "Select a node";
  qs("#detailSummary").textContent = "Click any card on the canvas to inspect citations, costs, confidence, and routing decisions.";
  qs("#detailTags").innerHTML = "";
  qs("#detailCost").innerHTML = "";
  qs("#detailSources").innerHTML = "";
  qs("#detailJson").textContent = "";
}

function renderDetails(node) {
  if (!node) {
    renderEmptyDetails();
    return;
  }
  qs("#detailTitle").textContent = node.title;
  qs("#detailSummary").textContent = node.summary;
  const tags = qs("#detailTags");
  tags.innerHTML = "";
  (node.tags || []).forEach((tag) => {
    const kind = tag.includes("risk") || tag.includes("dissent") ? "danger" : tag.includes("fork") ? "warn" : "";
    tags.appendChild(html("span", `chip ${kind}`, tag));
  });
  renderCost(node.cost);
  renderSources(node.sources || []);
  qs("#detailJson").textContent = JSON.stringify(node.details || {}, null, 2);
}

function renderCost(cost) {
  const target = qs("#detailCost");
  target.innerHTML = "";
  if (!cost) return;
  const dl = html("dl");
  const fields = [
    ["route", cost.route],
    ["model", cost.model || "n/a"],
    ["input tokens", cost.input_tokens || 0],
    ["output tokens", cost.output_tokens || 0],
    ["tool calls", cost.tool_calls || 0],
    ["cost", `$${Number(cost.total_cost_usd || 0).toFixed(4)}`],
    ["latency", cost.latency_ms ? `${cost.latency_ms}ms` : "n/a"],
  ];
  fields.forEach(([label, value]) => {
    dl.append(html("dt", null, label), html("dd", null, String(value)));
  });
  target.appendChild(dl);
}

function renderSources(sources) {
  const target = qs("#detailSources");
  target.innerHTML = "";
  if (!sources.length) return;
  const list = html("div", "source-list");
  sources.forEach((source) => {
    const card = html("div", "source-card");
    const link = html("a", null, source.title || source.url);
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    card.appendChild(link);
    if (source.snippet) card.appendChild(html("p", null, source.snippet));
    list.appendChild(card);
  });
  target.appendChild(list);
}

function replay() {
  state.replayIndex = 0;
  state.selectedId = "objective";
  const timer = setInterval(() => {
    state.replayIndex += 1;
    renderCanvas();
    if (state.replayIndex >= state.graph.nodes.length) clearInterval(timer);
  }, 430);
}

function fit() {
  const svg = qs("#canvas");
  svg.setAttribute("viewBox", "0 0 2100 850");
}

function exportJson() {
  const blob = new Blob([JSON.stringify(state.graph, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${state.graph.id || "forklens"}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

qs("#replay").addEventListener("click", replay);
qs("#fit").addEventListener("click", fit);
qs("#export").addEventListener("click", exportJson);
qs("#applyObjective").addEventListener("click", applyObjective);
qs("#resetScenario").addEventListener("click", resetScenario);
qs("#objectiveInput").addEventListener("input", () => {
  qs("#scenarioSelect").value = "custom";
});
qs("#scenarioSelect").addEventListener("change", (event) => {
  const selected = event.target.value;
  if (selected === "custom") {
    qs("#objectiveInput").focus();
    return;
  }
  updateUrl(selected);
  loadGraph(selected).catch(showLoadError);
});

function showLoadError(error) {
  qs("#title").textContent = "ForkLens load error";
  qs("#objective").textContent = error.message;
  setLoadStatus(error.message);
  renderEmptyDetails();
  console.error(error);
}

loadGraph().catch(showLoadError);
