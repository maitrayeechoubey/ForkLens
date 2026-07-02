from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .demo import datacenter_demo, relocation_demo
from .perplexity import PerplexityAPIError, PerplexityClient, message_text, normalize_sources

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_demo(args: argparse.Namespace) -> int:
    demos = {
        "datacenter": ("demo-datacenter.json", datacenter_demo),
        "relocation": ("demo-relocation.json", relocation_demo),
    }
    if args.kind == "all" and args.output:
        raise SystemExit("--output can only be used with --kind datacenter or --kind relocation")
    selected = demos.items() if args.kind == "all" else [(args.kind, demos[args.kind])]
    for _name, (filename, factory) in selected:
        canvas = factory()
        output = Path(args.output or ROOT / "data" / filename)
        write_json(output, canvas.to_dict())
        print(f"Wrote {output}")
        print(f"Open: python -m forklens.cli serve --graph /data/{output.name}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    client = PerplexityClient()
    result = client.search(args.query, max_results=args.max_results)
    print(json.dumps(result.data, indent=2, ensure_ascii=False))
    return 0


def cmd_sonar(args: argparse.Namespace) -> int:
    client = PerplexityClient()
    result = client.sonar(args.prompt, model=args.model, max_tokens=args.max_tokens)
    print(message_text(result.data))
    print("\n--- sources ---")
    print(json.dumps(normalize_sources(result.data), indent=2, ensure_ascii=False))
    print("\n--- usage ---")
    print(json.dumps(result.usage, indent=2, ensure_ascii=False))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    graph = args.graph or "/data/demo-relocation.json"
    os.chdir(ROOT)
    url = f"http://127.0.0.1:{args.port}/public/index.html?graph={graph}"
    print(f"Serving ForkLens at {url}")
    if args.open:
        webbrowser.open(url)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forklens", description="Forkable evidence canvas for Perplexity-powered research")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Write seeded demo canvases")
    demo.add_argument("--kind", choices=["datacenter", "relocation", "all"], default="all", help="Demo graph to write")
    demo.add_argument("--output", help="Output JSON path")
    demo.set_defaults(func=cmd_demo)

    serve = sub.add_parser("serve", help="Serve the static canvas viewer")
    serve.add_argument("--graph", default="/data/demo-relocation.json", help="Graph JSON URL relative to the server root")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--open", action="store_true", help="Open browser")
    serve.set_defaults(func=cmd_serve)

    search = sub.add_parser("search", help="Call Perplexity Search API")
    search.add_argument("query")
    search.add_argument("--max-results", type=int, default=10)
    search.set_defaults(func=cmd_search)

    sonar = sub.add_parser("sonar", help="Call Perplexity Sonar API")
    sonar.add_argument("prompt")
    sonar.add_argument("--model", default="sonar-pro")
    sonar.add_argument("--max-tokens", type=int)
    sonar.set_defaults(func=cmd_sonar)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PerplexityAPIError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
