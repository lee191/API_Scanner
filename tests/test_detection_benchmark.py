"""Detection benchmark — runs collect_path_candidates + collect_hardcoded_findings
on tests/fixtures/benchmark_site and asserts every expected pattern is found.

This file drives iterative enhancement: each EXPECTED row represents a real
modern API/path/secret shape we want detected. Add patterns -> entries flip
from miss to found.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from typing import Dict, List, Set, Tuple

from route_api_discovery import (
    Candidate,
    build_url_scope,
    collect_hardcoded_findings,
    collect_path_candidates,
    extract_html_assets,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "benchmark_site"
BASE_URL    = "https://bench.local/"


# (label, expected_path_substring) — value must appear as substring in
# the URL or path of one of the discovered candidates.
EXPECTED_PATHS: List[Tuple[str, str]] = [
    # baseline (already supported)
    ("fetch literal",          "/api/users"),
    ("axios.get",              "/api/orders"),
    ("axios.post",             "/api/cart"),
    ("axios object url",       "/api/checkout"),

    # modern wrappers
    ("ky.get",            "/api/profile"),
    ("got absolute",      "/v1/items"),
    ("superagent.get",    "/api/health"),

    # vue/nuxt
    ("$fetch",     "/api/nuxt/posts"),
    ("useFetch",   "/api/nuxt/items"),

    # navigation
    ("router.push",  "/dashboard"),
    ("useNavigate", "/profile"),
    ("svelte goto", "/svelte/route"),
    ("navigate",     "/orders/list"),

    # angular
    ("angular http.get",    "/api/angular/users"),
    ("angular http.post",   "/api/angular/login"),
    ("angular http.put",    "/api/angular/profile"),
    ("angular http.delete", "/api/angular/sessions/42"),

    # jquery
    ("$.ajax url",  "/api/jquery/list"),
    ("$.get",       "/api/jquery/get-only"),
    ("$.post",      "/api/jquery/post-only"),

    # custom client
    ("apiClient.get", "/api/custom/me"),
    ("api.users.list", "/api/custom/users"),

    # graphql endpoint
    ("graphql endpoint", "/graphql"),

    # realtime
    ("websocket", "/ws/notifications"),
    ("socket.io", "/realtime/chat"),
    ("sse",       "/api/sse/events"),

    # html resource hints
    ("link preload",  "/api/preload/init"),
    ("link prefetch", "/api/prefetch/menu"),

    # data attributes
    ("data-api",      "/api/data-attr/config"),
    ("data-endpoint", "/api/data-attr/users"),
    ("data-href",     "/admin/data-attr-page"),

    # next data
    ("next data endpoint", "/api/next-data/feed"),

    # inline
    ("inline fetch",  "/api/inline/health"),
    ("inline angular","/api/inline/angular"),

    # template literals with interpolation
    ("fetch tpl interp 1", "/api/users/:param/profile"),
    ("fetch tpl interp 2", "/api/:param/billing"),

    # legacy XHR
    ("xhr.open", "/api/xhr/legacy"),

    # Angular $resource
    ("$resource", "/api/resource/items/:id"),

    # Method chain
    ("chain client", "/api/chain/start"),

    # webpack/window config object
    ("window app config", "/api/v2"),
    ("ws base in config",  "/v2/ws"),
]


# Patterns that MUST NOT be flagged as API endpoints (false-positive guard).
NEGATIVE_PATHS: List[Tuple[str, str]] = [
    ("doc string",           "/api/docs"),
    ("commented example",    "/api/example-only"),
]


# (label, marker_in_matched_by) — finding's matched_by field must contain marker.
EXPECTED_SECRETS: List[Tuple[str, str]] = [
    ("postgres conn string", "postgres"),
    ("mysql conn string",    "mysql"),
    ("mongo conn string",    "mongodb"),
    ("redis conn string",    "redis"),
    ("slack webhook",  "slack_webhook"),
    ("discord webhook","discord_webhook"),
    ("twilio sid",     "twilio"),
    ("sendgrid key",   "sendgrid"),
]


def _load_fixture() -> Tuple[str, str]:
    html = (FIXTURE_DIR / "index.html").read_text(encoding="utf-8")
    js   = (FIXTURE_DIR / "app.js").read_text(encoding="utf-8")
    return html, js


def _gather_all_paths(html: str, js: str) -> Set[str]:
    """Run path collection on both HTML and JS, return URL+path set."""
    scope = build_url_scope(BASE_URL, include_subdomains=True, excluded_hostnames=())
    page_bucket: Dict[str, Candidate] = {}
    api_bucket:  Dict[str, Candidate] = {}

    collect_path_candidates(
        text=js, base_url=BASE_URL, source_label="js:app.js",
        scope=scope, page_bucket=page_bucket, api_bucket=api_bucket,
    )

    _, inline_scripts = extract_html_assets(html, BASE_URL, scope)
    for inline in inline_scripts:
        collect_path_candidates(
            text=inline, base_url=BASE_URL, source_label="inline-script",
            scope=scope, page_bucket=page_bucket, api_bucket=api_bucket,
        )

    collect_path_candidates(
        text=html, base_url=BASE_URL, source_label="html:index",
        scope=scope, page_bucket=page_bucket, api_bucket=api_bucket,
    )

    found: Set[str] = set()
    for cand in list(page_bucket.values()) + list(api_bucket.values()):
        found.add(cand.url)
        found.add(cand.path)
    return found


def _gather_all_secrets(html: str, js: str) -> List[dict]:
    findings: List[dict] = []
    dedupe_keys: set = set()
    collect_hardcoded_findings(
        text=js, source_url="https://bench.local/app.js",
        source_label="js:app.js", source_type="js",
        findings=findings, dedupe_keys=dedupe_keys,
    )
    collect_hardcoded_findings(
        text=html, source_url=BASE_URL,
        source_label="html:index", source_type="html",
        findings=findings, dedupe_keys=dedupe_keys,
    )
    return findings


class DetectionBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html, cls.js = _load_fixture()
        cls.paths = _gather_all_paths(cls.html, cls.js)
        cls.secrets = _gather_all_secrets(cls.html, cls.js)

    def test_path_coverage(self) -> None:
        misses: List[str] = []
        for label, needle in EXPECTED_PATHS:
            if not any(needle in p for p in self.paths):
                misses.append(f"  - {label}: expected substring {needle!r}")
        if misses:
            sample = "\n    ".join(sorted(self.paths)[:80])
            self.fail(
                f"Path detection misses ({len(misses)}/{len(EXPECTED_PATHS)}):\n"
                + "\n".join(misses)
                + f"\n\nDetected paths sample (first 80):\n    {sample}"
            )

    def test_negative_paths_not_falsely_flagged(self) -> None:
        # These strings appear in comments / help text / docs and should NOT
        # be classified as discovered endpoints.
        false_hits: List[str] = []
        for label, needle in NEGATIVE_PATHS:
            for path in self.paths:
                if needle in path:
                    false_hits.append(f"  - {label}: {path!r}")
        if false_hits:
            self.fail("Negative path fixtures were classified as endpoints:\n" + "\n".join(false_hits))

    def test_secret_coverage(self) -> None:
        matched_by = [str(f.get("matched_by", "")) for f in self.secrets]
        misses: List[str] = []
        for label, marker in EXPECTED_SECRETS:
            if not any(marker in m for m in matched_by):
                misses.append(f"  - {label}: expected matched_by contains {marker!r}")
        if misses:
            self.fail(
                f"Secret detection misses ({len(misses)}/{len(EXPECTED_SECRETS)}):\n"
                + "\n".join(misses)
                + f"\n\nDetected matched_by values:\n    "
                + "\n    ".join(sorted(set(matched_by)))
            )


if __name__ == "__main__":
    unittest.main()
