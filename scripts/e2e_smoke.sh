#!/usr/bin/env bash
# Secret-safe end-to-end smoke test for the locally running demo.
# Usage: ./scripts/e2e_smoke.sh [backend_url] [frontend_url]
set -euo pipefail

BACKEND_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:5173}"

fail() { echo "FAIL: $*" >&2; exit 1; }
get_json() { curl --fail --silent --show-error --max-time 10 "$1"; }

echo "Smoke testing backend: $BACKEND_URL"
health="$(get_json "$BACKEND_URL/health")"
python3 -c 'import json,sys; assert json.load(sys.stdin).get("status") == "ok"' <<<"$health" \
  || fail "health response was not {status: ok}"

status="$(get_json "$BACKEND_URL/catalog/status")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d.get("loaded"),bool); assert isinstance(d.get("product_count"),int); assert isinstance(d.get("ai_enabled"),bool)' <<<"$status" \
  || fail "catalog status contract is invalid"
status_summary="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("{} products, ai_enabled={}".format(d["product_count"], d["ai_enabled"]))' <<<"$status")" \
  || fail "catalog status summary could not be parsed"
echo "  catalog status: $status_summary"

search="$(get_json "$BACKEND_URL/search?q=wireless%20headphones&curate=false&page_size=5")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["query"] == "wireless headphones"; assert len(d["results"]) <= 5; assert d["page"] == 1; assert d["page_size"] == 5; assert all("product" in x and "bm25_rank" in x for x in d["results"])' <<<"$search" \
  || fail "deterministic search contract failed"
search_count="$(python3 -c 'import json,sys; print(len(json.load(sys.stdin)["results"]))' <<<"$search")" \
  || fail "deterministic search summary could not be parsed"
echo "  deterministic search: $search_count results"

nomatch="$(get_json "$BACKEND_URL/search?q=smoke-no-such-product-xyz&curate=false")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["results"] == []; assert d["total_results"] == 0' <<<"$nomatch" \
  || fail "no-match search did not return an empty result set"

if curl --fail --silent --show-error --max-time 10 "$BACKEND_URL/search?q=wireless%20headphones&page=0" >/dev/null 2>&1; then
  fail "invalid page unexpectedly succeeded"
fi
echo "  validation/no-match: passed"

cors_headers="$(curl --fail --silent --show-error --max-time 10 -i -X OPTIONS "$BACKEND_URL/search" \
  -H 'Origin: http://127.0.0.1:5173' \
  -H 'Access-Control-Request-Method: GET')"
grep -qi '^access-control-allow-origin: http://127.0.0.1:5173' <<<"$cors_headers" \
  || fail "CORS did not allow the local 127.0.0.1 frontend"
echo "  CORS preflight: passed"

frontend_headers="$(curl --fail --silent --show-error --max-time 10 -I "$FRONTEND_URL/")"
grep -q '^HTTP/.* 200' <<<"$frontend_headers" || fail "frontend did not return HTTP 200"
echo "  frontend: HTTP 200 at $FRONTEND_URL/"
echo "PASS: local end-to-end smoke checks completed"
