import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from route_api_discovery import (
    build_saved_js_filename,
    build_summary_lines,
    build_batch_result,
    build_url_scope,
    collect_hardcoded_findings,
    Config,
    FetchResult,
    MAX_RESPONSE_BYTES,
    RecursiveDiscoveryState,
    discover,
    _discover_once,
    extract_html_assets,
    fetch_text,
    get_domain_key,
    is_http_url,
    normalize_path,
    parse_hostname_filters,
    parse_header_lines,
    probe_candidate,
    read_response_text,
    resolve_sensitive_findings,
    validate_js_output_dir,
)
from route_api_discovery_qt import ScanRequest, ScanWorker


class _DummyHeaders:
    def get_content_charset(self):
        return "utf-8"


class _DummyResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.headers = _DummyHeaders()

    def read(self, amount: int = -1) -> bytes:
        if amount < 0:
            return self._payload
        return self._payload[:amount]


def _minimal_batch_result() -> dict:
    return {
        "input_urls": ["https://example.com"],
        "success_count": 1,
        "failed_count": 0,
        "results": [
            {
                "input_url": "https://example.com",
                "summary": {
                    "js_discovered": 0,
                    "js_fetched": 0,
                    "page_count": 0,
                    "api_count": 0,
                },
            }
        ],
    }


class CodeReviewAlignmentTests(unittest.TestCase):
    def test_normalize_path_keeps_query_string(self) -> None:
        self.assertEqual(normalize_path("https://example.com/api/user?id=1"), "/api/user?id=1")

    def test_is_http_url_rejects_private_and_local_hosts(self) -> None:
        self.assertTrue(is_http_url("https://example.com/api"))
        self.assertFalse(is_http_url("http://localhost:8000"))
        self.assertFalse(is_http_url("http://127.0.0.1/test"))
        self.assertFalse(is_http_url("http://10.0.0.5/test"))

    def test_parse_hostname_filters_supports_comma_separated_hostnames(self) -> None:
        filters = parse_hostname_filters(["cdn.example.com, *.static.example.com  cdn.example.com"])

        self.assertEqual(filters, ("cdn.example.com", "static.example.com"))

    def test_parse_header_lines_rejects_control_chars(self) -> None:
        with self.assertRaisesRegex(ValueError, "제어 문자"):
            parse_header_lines("X-Test: ok\x00bad")

    def test_read_response_text_rejects_oversized_payload(self) -> None:
        response = _DummyResponse(b"a" * (MAX_RESPONSE_BYTES + 1))

        with self.assertRaisesRegex(ValueError, "응답 크기 제한"):
            read_response_text(response)

    def test_fetch_text_handles_oserror_without_raising(self) -> None:
        with patch("route_api_discovery.urlopen", side_effect=OSError("connection reset")):
            result = fetch_text("https://example.com", timeout=1.0)

        self.assertFalse(result.success)
        self.assertIn("connection reset", result.error or "")

    def test_probe_candidate_tries_get_before_post(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            calls.append(method)
            if method == "GET":
                return FetchResult(url=url, status_code=405, text="", success=False, length=0, error="Method Not Allowed")
            if method == "POST":
                return FetchResult(url=url, status_code=200, text="", success=True, length=0)
            self.fail(f"unexpected method: {method}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = probe_candidate("https://example.com/api/users", kind="api", timeout=1.0)

        self.assertTrue(result.accessible)
        self.assertEqual(result.method, "POST")
        self.assertEqual(calls, ["GET", "POST"])

    def test_get_domain_key_groups_same_site_subdomains(self) -> None:
        self.assertEqual(
            get_domain_key("https://csatreportcard.kice.re.kr/main.do"),
            get_domain_key("https://csatcdn.kice.re.kr/js/common.js"),
        )
        self.assertNotEqual(
            get_domain_key("https://csatreportcard.kice.re.kr/main.do"),
            get_domain_key("https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"),
        )

    def test_extract_html_assets_keeps_same_site_script_without_js_suffix(self) -> None:
        root_url = "https://app.example.co.kr/index"
        scope = build_url_scope(root_url)
        html = '<script src="https://static.example.co.kr/runtime/main?build=20260409"></script>'

        script_urls, inline_scripts = extract_html_assets(html, root_url, scope)

        self.assertEqual(script_urls, ["https://static.example.co.kr/runtime/main?build=20260409"])
        self.assertEqual(inline_scripts, [])

    def test_extract_html_assets_can_limit_matching_to_exact_host(self) -> None:
        root_url = "https://app.example.co.kr/index"
        scope = build_url_scope(root_url, include_subdomains=False)
        html = '<script src="https://static.example.co.kr/runtime/main?build=20260409"></script>'

        script_urls, inline_scripts = extract_html_assets(html, root_url, scope)

        self.assertEqual(script_urls, [])
        self.assertEqual(inline_scripts, [])

    def test_extract_html_assets_skips_excluded_subdomain(self) -> None:
        root_url = "https://app.example.co.kr/index"
        scope = build_url_scope(root_url, excluded_hostnames=("static.example.co.kr",))
        html = '<script src="https://static.example.co.kr/runtime/main?build=20260409"></script>'

        script_urls, inline_scripts = extract_html_assets(html, root_url, scope)

        self.assertEqual(script_urls, [])
        self.assertEqual(inline_scripts, [])

    def test_discover_once_tracks_discovered_vs_fetched_js_counts(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        root_html = '<html><script src="/a.js"></script><script src="/b.js"></script></html>'

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            if url == "https://example.com/a.js":
                return FetchResult(url=url, status_code=200, text="console.log('a')", success=True, length=16)
            self.fail(f"unexpected fetch: {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = _discover_once(config, "https://example.com", state=RecursiveDiscoveryState())

        self.assertEqual(result["summary"]["js_discovered"], 2)
        self.assertEqual(result["summary"]["js_fetched"], 1)

    def test_discover_once_does_not_count_failed_js_against_fetch_limit(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        root_html = '<html><script src="/a.js"></script><script src="/b.js"></script></html>'

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            if url == "https://example.com/a.js":
                return FetchResult(url=url, status_code=404, text="", success=False, length=0, error="HTTP Error 404: Not Found")
            if url == "https://example.com/b.js":
                return FetchResult(url=url, status_code=200, text="console.log('b')", success=True, length=16)
            self.fail(f"unexpected fetch: {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = _discover_once(config, "https://example.com", state=RecursiveDiscoveryState())

        self.assertEqual(result["summary"]["js_discovered"], 2)
        self.assertEqual([item["url"] for item in result["js_files"]], ["https://example.com/a.js", "https://example.com/b.js"])
        self.assertEqual(sum(1 for item in result["js_files"] if item["success"]), 1)

    def test_discover_once_saves_successful_js_files_when_output_dir_is_set(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            config = Config(
                url="https://example.com",
                max_js_files=1,
                max_depth=0,
                timeout=1.0,
                output=Path("discovery-result.json"),
                skip_probe=False,
                js_output_dir=Path(tmp_dir),
            )
            root_html = '<html><script src="/assets/app.js?v=1"></script></html>'
            js_text = "console.log('saved')"

            def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
                if url == "https://example.com":
                    return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
                if url == "https://example.com/assets/app.js?v=1":
                    return FetchResult(url=url, status_code=200, text=js_text, success=True, length=len(js_text))
                self.fail(f"unexpected fetch: {url}")

            with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
                result = _discover_once(config, "https://example.com", state=RecursiveDiscoveryState())

            expected_path = Path(tmp_dir) / build_saved_js_filename("https://example.com/assets/app.js?v=1", 1)
            self.assertEqual(result["summary"]["js_saved"], 1)
            self.assertEqual(result["js_files"][0]["saved_path"], str(expected_path.resolve()))
            self.assertEqual(expected_path.read_text(encoding="utf-8"), js_text)

    def test_discover_once_records_js_save_error_without_failing_scan(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
            js_output_dir=Path("js-files"),
        )
        root_html = '<html><script src="/app.js"></script></html>'
        js_text = "console.log('still scanned')"

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            if url == "https://example.com/app.js":
                return FetchResult(url=url, status_code=200, text=js_text, success=True, length=len(js_text))
            self.fail(f"unexpected fetch: {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch), patch(
            "route_api_discovery.save_js_file",
            side_effect=OSError("disk full"),
        ):
            result = _discover_once(config, "https://example.com", state=RecursiveDiscoveryState())

        self.assertEqual(result["summary"]["js_saved"], 0)
        self.assertEqual(result["summary"]["js_fetched"], 1)
        self.assertEqual(result["js_files"][0]["saved_path"], "")
        self.assertIn("disk full", result["js_files"][0]["save_error"])

    def test_validate_js_output_dir_rejects_windows_reserved_path_parts(self) -> None:
        with self.assertRaisesRegex(ValueError, "Windows"):
            validate_js_output_dir(Path("CON") / "js")

    def test_discover_recursively_scans_accessible_200_pages_and_their_js(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=5,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
            recursive_scan=True,
            recursive_depth=1,
        )
        root_html = '<html><script src="/root.js"></script></html>'
        root_js = 'const nextPage = "/about";'
        about_html = '<html><script src="/about.js"></script></html>'
        about_js = 'fetch("/api/about")'

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if method == "GET" and url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            if method == "GET" and url == "https://example.com/root.js":
                return FetchResult(url=url, status_code=200, text=root_js, success=True, length=len(root_js))
            if method == "GET" and url == "https://example.com/about":
                return FetchResult(url=url, status_code=200, text=about_html, success=True, length=len(about_html))
            if method == "GET" and url == "https://example.com/about.js":
                return FetchResult(url=url, status_code=200, text=about_js, success=True, length=len(about_js))
            if method == "GET" and url == "https://example.com/api/about":
                return FetchResult(url=url, status_code=200, text="", success=True, length=0)
            self.fail(f"unexpected fetch: {method} {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = discover(config)

        self.assertEqual(result["recursive_scanned_targets"], ["https://example.com", "https://example.com/about"])
        self.assertIn("https://example.com/about", result["recursive_discovered_targets"])
        self.assertTrue(any(item["url"] == "https://example.com/about.js" for item in result["js_files"]))
        self.assertTrue(any(item["path"] == "/api/about" for item in result["all_apis"]))

    def test_discover_skips_excluded_subdomain_targets(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=5,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
            recursive_scan=True,
            recursive_depth=1,
            include_subdomains=True,
            excluded_subdomains=("cdn.example.com",),
        )
        root_html = '<html><script src="/root.js"></script></html>'
        root_js = 'const nextPage = "https://cdn.example.com/about";'

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if method == "GET" and url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            if method == "GET" and url == "https://example.com/root.js":
                return FetchResult(url=url, status_code=200, text=root_js, success=True, length=len(root_js))
            self.fail(f"unexpected fetch: {method} {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = discover(config)

        self.assertEqual(result["recursive_scanned_targets"], ["https://example.com"])
        self.assertEqual(result["recursive_discovered_targets"], [])
        self.assertEqual(result["excluded_subdomains"], ["cdn.example.com"])

    def test_discover_once_collects_hardcoded_findings_from_html_inline_and_js(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=2,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        root_html = (
            "<html>"
            "support@company.co.kr"
            "<script>"
            "const fullName = '홍길동';"
            "const accountId = 'ACCT-1024';"
            "const token = 'sk_live_123456789';"
            "</script>"
            "<script src='/app.js'></script>"
            "</html>"
        )
        js_text = "const phone = '010-1234-5678'; const userId = 'hong01';"

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            if url == "https://example.com/app.js":
                return FetchResult(url=url, status_code=200, text=js_text, success=True, length=len(js_text))
            self.fail(f"unexpected fetch: {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = _discover_once(config, "https://example.com", state=RecursiveDiscoveryState())

        findings = result.get("hardcoded_findings", [])
        categories = {item.get("category") for item in findings}
        self.assertTrue({"email", "person_name", "account_id", "token", "phone", "user_id"}.issubset(categories))
        self.assertEqual(result["summary"]["hardcoded_total"], len(findings))
        self.assertGreaterEqual(result["summary"]["hardcoded_high_or_above"], 1)
        self.assertGreaterEqual(result["summary"]["hardcoded_pii_count"], 1)
        self.assertGreaterEqual(result["summary"]["hardcoded_secret_count"], 1)
        self.assertIn("hardcoded_summary", result)
        self.assertIn("by_category", result["hardcoded_summary"])
        required_keys = {
            "category",
            "field_name",
            "value",
            "masked_value",
            "normalized_value",
            "source_type",
            "source_url",
            "source_label",
            "line",
            "column",
            "context",
            "confidence",
            "severity",
            "matched_by",
        }
        self.assertTrue(required_keys.issubset(findings[0].keys()))

    def test_discover_once_ignores_env_reference_literals_for_secrets(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        root_html = (
            "<html><script>"
            "const apiKey = '${process.env.API_KEY}';"
            "const refreshToken = '${TOKEN}';"
            "const email = 'real.user@company.co.kr';"
            "</script></html>"
        )

        def fake_fetch(url: str, timeout: float, method: str = "GET", headers=None, execution=None, verify_ssl: bool = True):
            if url == "https://example.com":
                return FetchResult(url=url, status_code=200, text=root_html, success=True, length=len(root_html))
            self.fail(f"unexpected fetch: {url}")

        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            result = _discover_once(config, "https://example.com", state=RecursiveDiscoveryState())

        findings = result.get("hardcoded_findings", [])
        self.assertTrue(any(item.get("category") == "email" for item in findings))
        self.assertFalse(any(item.get("category") == "token" for item in findings))
        self.assertFalse(any("process.env" in str(item.get("value", "")).lower() for item in findings))
        self.assertFalse(any("${" in str(item.get("value", "")) for item in findings))

    def test_build_batch_result_sums_hardcoded_summary_fields(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        records = [
            {
                "status": "success",
                "summary": {
                    "js_discovered": 1,
                    "js_fetched": 1,
                    "page_count": 1,
                    "api_count": 1,
                    "hardcoded_total": 3,
                    "hardcoded_high_or_above": 2,
                    "hardcoded_pii_count": 2,
                    "hardcoded_secret_count": 1,
                },
            },
            {
                "status": "error",
                "summary": {
                    "js_discovered": 0,
                    "js_fetched": 0,
                    "page_count": 0,
                    "api_count": 0,
                    "hardcoded_total": 1,
                    "hardcoded_high_or_above": 0,
                    "hardcoded_pii_count": 1,
                    "hardcoded_secret_count": 0,
                },
            },
        ]

        batch = build_batch_result(records, ["https://example.com", "https://example.org"], config)

        self.assertEqual(batch["summary"]["hardcoded_total"], 4)
        self.assertEqual(batch["summary"]["hardcoded_high_or_above"], 2)
        self.assertEqual(batch["summary"]["hardcoded_pii_count"], 3)
        self.assertEqual(batch["summary"]["hardcoded_secret_count"], 1)
        self.assertEqual(batch["summary"]["sensitive_total"], 4)
        self.assertEqual(batch["summary"]["sensitive_high_or_above"], 2)

    def test_collect_hardcoded_findings_ignores_generic_html_name_attributes(self) -> None:
        text = '<meta name="viewport" content="width=device-width"><input name="username">'
        findings: list[dict] = []
        dedupe_keys: set[tuple[str, str, str, str, int, int]] = set()

        collect_hardcoded_findings(
            text=text,
            source_url="https://example.com",
            source_label="html:https://example.com",
            source_type="html",
            findings=findings,
            dedupe_keys=dedupe_keys,
        )

        self.assertFalse(any(item.get("category") == "person_name" for item in findings))

    def test_collect_hardcoded_findings_keeps_duplicates_from_different_inline_blocks(self) -> None:
        findings: list[dict] = []
        dedupe_keys: set[tuple[str, str, str, str, int, int]] = set()

        collect_hardcoded_findings(
            text="const token = 'abc123';",
            source_url="https://example.com",
            source_label="inline-script:https://example.com#1",
            source_type="inline_script",
            findings=findings,
            dedupe_keys=dedupe_keys,
        )
        collect_hardcoded_findings(
            text="const token = 'abc123';",
            source_url="https://example.com",
            source_label="inline-script:https://example.com#2",
            source_type="inline_script",
            findings=findings,
            dedupe_keys=dedupe_keys,
        )

        token_findings = [item for item in findings if item.get("category") == "token"]
        self.assertEqual(len(token_findings), 2)

    def test_collect_hardcoded_findings_requires_context_for_international_phone(self) -> None:
        findings: list[dict] = []
        dedupe_keys: set[tuple[str, str, str, str, int, int]] = set()

        collect_hardcoded_findings(
            text="const misc = '001-234-567-890';",
            source_url="https://example.com/app.js",
            source_label="js:https://example.com/app.js",
            source_type="js",
            findings=findings,
            dedupe_keys=dedupe_keys,
        )
        self.assertFalse(any(item.get("category") == "phone" for item in findings))

        collect_hardcoded_findings(
            text="const phone = '001-234-567-890';",
            source_url="https://example.com/app.js",
            source_label="js:https://example.com/app.js#2",
            source_type="js",
            findings=findings,
            dedupe_keys=dedupe_keys,
        )
        self.assertTrue(any(item.get("category") == "phone" for item in findings))

    def test_build_summary_lines_reads_sensitive_alias_keys(self) -> None:
        result = {
            "input_url": "https://example.com",
            "scanned_at": "2026-04-08T13:00:00+09:00",
            "status": "success",
            "summary": {
                "js_fetched": 0,
                "page_count": 0,
                "api_count": 0,
                "sensitive_total": 1,
                "sensitive_high_or_above": 1,
                "sensitive_pii_count": 1,
                "sensitive_secret_count": 0,
            },
            "probe_skipped": False,
            "include_subdomains": True,
            "excluded_subdomains": [],
            "max_workers": 1,
            "request_delay": 0.0,
            "recursive_enabled": False,
            "recursive_depth": 0,
            "recursive_total_scans": 1,
            "recursive_discovered_targets": [],
            "recursive_failed_targets": [],
            "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
            "accessible_pages": [],
            "accessible_apis": [],
            "sensitive_findings": [
                {
                    "category": "email",
                    "masked_value": "a***@example.com",
                    "confidence": 0.95,
                    "severity": "high",
                }
            ],
            "hardcoded_findings": [],
        }

        lines = build_summary_lines(result, Path("discovery-result.json"), language="en")
        self.assertTrue(any("Hardcoded findings: 1" in line for line in lines))

    def test_resolve_sensitive_findings_falls_back_when_hardcoded_list_is_empty(self) -> None:
        result = {
            "hardcoded_findings": [],
            "sensitive_findings": [
                {"category": "email", "value": "a@example.com", "source_type": "js", "source_label": "js:x", "line": 1, "column": 1}
            ],
        }

        findings = resolve_sensitive_findings(result)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].get("category"), "email")

    def test_scan_worker_emits_finished_without_saving_results(self) -> None:
        request = ScanRequest(
            urls=["https://example.com"],
            config=Config(
                url="https://example.com",
                max_js_files=1,
                max_depth=0,
                timeout=1.0,
                output=Path("discovery-result.json"),
                skip_probe=False,
            ),
        )
        worker = ScanWorker(request)
        failed_events: list[str] = []
        finished_events: list[dict] = []

        worker.failed.connect(lambda message: failed_events.append(message))
        worker.finished.connect(lambda result: finished_events.append(result))

        with patch("route_api_discovery_qt.discover_many", return_value=_minimal_batch_result()):
            worker.run()

        self.assertEqual(failed_events, [])
        self.assertEqual(finished_events, [_minimal_batch_result()])


if __name__ == "__main__":
    unittest.main()
