from __future__ import annotations

import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import Request

import route_api_discovery as discovery


class RedirectSafetyTests(unittest.TestCase):
    def test_blocks_private_redirect_from_public_source(self) -> None:
        with self.assertRaises(URLError):
            discovery.validate_redirect_target(
                "https://example.com/start",
                "http://127.0.0.1/admin",
            )

    def test_allows_relative_public_redirect(self) -> None:
        self.assertEqual(
            discovery.validate_redirect_target(
                "https://example.com/start",
                "/next",
            ),
            "https://example.com/next",
        )

    def test_allows_private_redirect_for_explicit_private_scan(self) -> None:
        self.assertEqual(
            discovery.validate_redirect_target(
                "http://127.0.0.1/start",
                "/next",
                allow_disallowed_host=True,
            ),
            "http://127.0.0.1/next",
        )

    def test_cross_origin_redirect_drops_custom_headers(self) -> None:
        handler = discovery.SafeRedirectHandler()
        request = Request(
            "https://example.com/start",
            headers={"Authorization": "Bearer secret", "X-Trace-Id": "trace"},
        )

        redirected = handler.redirect_request(request, None, 302, "Found", {}, "https://other.example/next")

        self.assertIsNotNone(redirected)
        redirected_headers = {key.lower(): value for key, value in redirected.header_items()}
        self.assertNotIn("authorization", redirected_headers)
        self.assertNotIn("x-trace-id", redirected_headers)

    def test_same_origin_redirect_preserves_custom_headers(self) -> None:
        handler = discovery.SafeRedirectHandler()
        request = Request(
            "https://example.com/start",
            headers={"Authorization": "Bearer secret"},
        )

        redirected = handler.redirect_request(request, None, 302, "Found", {}, "/next")

        self.assertEqual(dict(redirected.header_items())["Authorization"], "Bearer secret")


class HeaderForwardingTests(unittest.TestCase):
    def test_custom_headers_stay_on_trusted_origin(self) -> None:
        headers = {"Authorization": "Bearer secret", "X-Trace-Id": "trace", "Accept-Language": "ko"}

        same_origin = discovery.request_headers_for_target(headers, "https://example.com", "https://example.com/api")
        other_origin = discovery.request_headers_for_target(headers, "https://example.com", "https://api.example.com/api")

        self.assertEqual(same_origin, headers)
        self.assertEqual(other_origin, {"Accept-Language": "ko"})


class ProbeSafetyTests(unittest.TestCase):
    def test_probe_uses_head_then_get_without_post(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str, **kwargs) -> discovery.FetchResult:
            method = kwargs["method"]
            calls.append(method)
            if method == "HEAD":
                return discovery.FetchResult(url, 405, "", False, 0, error="method not allowed")
            return discovery.FetchResult(url, 200, "ok", True, 2)

        with patch.object(discovery, "fetch_text", side_effect=fake_fetch):
            result = discovery.probe_candidate("https://example.com/api/items", "api", 1.0)

        self.assertTrue(result.accessible)
        self.assertEqual(result.method, "GET")
        self.assertEqual(calls, ["HEAD", "GET"])
        self.assertNotIn("POST", calls)

    def test_probe_stops_after_successful_head(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str, **kwargs) -> discovery.FetchResult:
            calls.append(kwargs["method"])
            return discovery.FetchResult(url, 200, "", True, 0)

        with patch.object(discovery, "fetch_text", side_effect=fake_fetch):
            result = discovery.probe_candidate("https://example.com/health", "api", 1.0)

        self.assertTrue(result.accessible)
        self.assertEqual(result.method, "HEAD")
        self.assertEqual(calls, ["HEAD"])


class CancellationTests(unittest.TestCase):
    def test_wait_with_cancellation_aborts_immediately(self) -> None:
        execution = discovery.ExecutionContext(
            max_workers=1,
            request_throttle=discovery.RequestThrottle(),
            cancel_event=threading.Event(),
        )
        execution.cancel_event.set()

        with self.assertRaises(discovery.ScanCancelled):
            discovery.wait_with_cancellation(10, execution)


class CandidateIdentityTests(unittest.TestCase):
    def test_normalize_path_preserves_query_string(self) -> None:
        self.assertEqual(
            discovery.normalize_path("https://example.com/api/items?page=2"),
            "/api/items?page=2",
        )


class HeaderValidationTests(unittest.TestCase):
    def test_single_header_entry_uses_common_validation(self) -> None:
        self.assertEqual(
            discovery.parse_header_entry("X-Trace-Id", " abc "),
            ("X-Trace-Id", "abc"),
        )

    def test_single_header_entry_rejects_colon_in_name(self) -> None:
        with self.assertRaises(ValueError):
            discovery.parse_header_entry("X-Bad: injected", "value")


class ScopeSafetyTests(unittest.TestCase):
    def test_include_subdomains_does_not_include_sibling_tenant(self) -> None:
        scope = discovery.build_url_scope("https://tenant-a.github.io", include_subdomains=True)

        self.assertTrue(discovery.url_matches_scope("https://assets.tenant-a.github.io/app.js", scope))
        self.assertFalse(discovery.url_matches_scope("https://tenant-b.github.io/app.js", scope))


class DiscoveryRedirectTests(unittest.TestCase):
    def test_redirected_document_uses_final_url_for_relative_assets(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path == "/start":
                    self.send_response(302)
                    self.send_header("Location", "/app/")
                    self.end_headers()
                    return
                if self.path == "/app/":
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'<script src="assets/app.js"></script><script>fetch("api/items")</script>')
                    return
                if self.path == "/app/assets/app.js":
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"fetch('../api/from-js')")
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *_args) -> None:
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            root = f"http://127.0.0.1:{server.server_port}/start"
            config = discovery.Config(
                url=root,
                max_js_files=5,
                max_depth=1,
                timeout=2,
                output=Path("unused.json"),
                skip_probe=True,
            )

            result = discovery.discover(config)

            self.assertEqual(result["final_url"], f"http://127.0.0.1:{server.server_port}/app/")
            self.assertEqual(result["js_files"][0]["url"], f"http://127.0.0.1:{server.server_port}/app/assets/app.js")
            self.assertIn("/app/api/items", {item["path"] for item in result["all_apis"]})
            self.assertIn("/app/api/from-js", {item["path"] for item in result["all_apis"]})
        finally:
            server.shutdown()
            server.server_close()

    def test_failed_js_requests_respect_max_js_files_limit(self) -> None:
        requested_paths: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                requested_paths.append(self.path)
                if self.path == "/":
                    self.send_response(200)
                    self.end_headers()
                    scripts = "".join(f'<script src="/missing-{index}.js"></script>' for index in range(5))
                    self.wfile.write(scripts.encode())
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *_args) -> None:
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            config = discovery.Config(
                url=f"http://127.0.0.1:{server.server_port}/",
                max_js_files=1,
                max_depth=1,
                timeout=2,
                output=Path("unused.json"),
                skip_probe=True,
            )

            result = discovery.discover(config)

            self.assertEqual(len(result["js_files"]), 1)
            self.assertEqual(len([path for path in requested_paths if path.startswith("/missing-")]), 1)
        finally:
            server.shutdown()
            server.server_close()


class SensitiveOutputTests(unittest.TestCase):
    def test_hardcoded_secret_output_retains_plaintext_and_masked_value(self) -> None:
        findings: list[dict] = []
        discovery.collect_hardcoded_findings(
            text='const password = "SuperSecret123!";',
            source_url="https://example.com/app.js",
            source_label="js:https://example.com/app.js",
            source_type="js",
            findings=findings,
            dedupe_keys=set(),
        )

        self.assertEqual(len(findings), 1)
        serialized = repr(findings)
        self.assertIn("SuperSecret123!", serialized)
        self.assertEqual(findings[0]["value"], "SuperSecret123!")
        self.assertEqual(findings[0]["masked_value"], "********")
        self.assertIn("SuperSecret123!", findings[0]["context"])
        self.assertTrue(findings[0]["normalized_value"].startswith("sha256:"))

    def test_proxy_credentials_are_redacted_for_output(self) -> None:
        self.assertEqual(
            discovery.redact_url_credentials("http://user:password@proxy.example:8080"),
            "http://***:***@proxy.example:8080",
        )


class SensitiveGuiDisplayTests(unittest.TestCase):
    def test_ctk_sensitive_row_prefers_plaintext_value(self) -> None:
        from route_api_discovery_ctk import CtkDiscoveryApp

        app = object.__new__(CtkDiscoveryApp)
        rows = app._build_rows(
            {
                "sensitive_findings": [
                    {
                        "category": "credential",
                        "value": "SuperSecret123!",
                        "masked_value": "********",
                    }
                ]
            }
        )

        sensitive_row = next(row for row in rows if row["kind"] == "sensitive")
        self.assertEqual(sensitive_row["value"], "SuperSecret123!")


class CliSafetyDefaultsTests(unittest.TestCase):
    def test_dynamic_actions_require_explicit_opt_in(self) -> None:
        args = discovery.parse_args(["https://example.com", "--dynamic-analysis"])

        self.assertFalse(args.dynamic_actions)


if __name__ == "__main__":
    unittest.main()
