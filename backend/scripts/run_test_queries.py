"""Runs every query in data/test_queries.json against the real search
pipeline and writes a human-readable report to backend/TEST_RESULTS.md.

This is the "test input and output" deliverable for the assignment — run
it against the full 225-product catalog (not a test fixture) so the
report reflects real search behavior. AI curation tags are included if
GEMINI_API_KEY is set in the environment; otherwise the report reflects
the deterministic ranking only (also valid, just without tags).

Usage (from backend/, with the venv active and Qdrant running via
`docker compose up -d`):
    ./venv/bin/python scripts/run_test_queries.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient

# Make the documented ``python scripts/run_test_queries.py`` invocation work
# when launched from ``backend/`` (Python otherwise adds only ``scripts/``).
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_QUERIES_FILE = REPO_ROOT / "data" / "test_queries.json"
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "TEST_RESULTS.md"
TOP_N = 5


def main() -> None:
    queries = json.loads(TEST_QUERIES_FILE.read_text(encoding="utf-8"))

    lines = ["# Test Query Results", ""]
    observed_tags: set[str] = set()
    semantic_ready = False
    with TestClient(app) as client:
        semantic_ready = bool(getattr(app.state, "embeddings_ready", False))
        for entry in queries:
            query = entry["query"]
            notes = entry.get("notes", "")
            response = client.get("/search", params={"q": query, "page_size": TOP_N})

            lines.append(f'## "{query}"')
            lines.append("")
            if notes:
                lines.append(f"*Intended evaluation target:* {notes}")
                lines.append("")

            if response.status_code != 200:
                lines.append(f"**Request failed:** {response.status_code} {response.text}")
                lines.append("")
                continue

            body = response.json()
            lines.append(f"Applied filters: `{body['applied_filters']}`")
            lines.append("")
            lines.append(f"Total matches: {body['total_results']}")
            lines.append("")

            if not body["results"]:
                lines.append("_No results._")
                lines.append("")
                continue

            lines.append(
                "| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |"
            )
            lines.append(
                "|---|-------|----------|-------|-----------|----------------|-------------|-----|"
            )
            for i, result in enumerate(body["results"], start=1):
                product = result["product"]
                tag = result.get("tag") or ""
                if tag:
                    observed_tags.add(tag)
                lines.append(
                    f"| {i} | {product['title']} | {product['category']} | "
                    f"₹{product['price']:.0f} | {result['bm25_rank']} | "
                    f"{result['semantic_rank']} | {result['fused_score']:.4f} | "
                    f"{tag} |"
                )
            lines.append("")

    key_configured = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    if key_configured and observed_tags:
        ai_mode = "TAGS RETURNED"
    elif key_configured:
        ai_mode = "CONFIGURED BUT NO TAGS/FALLBACK"
    else:
        ai_mode = "NOT CONFIGURED"
    provenance = [
        "## Run provenance",
        "",
        f"- Semantic index: **{'READY' if semantic_ready else 'BM25 FALLBACK'}**",
        f"- AI curation: **{ai_mode}** (key presence only; key value is never reported)",
        "",
    ]
    lines[2:2] = provenance

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
