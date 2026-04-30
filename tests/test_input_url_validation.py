import unittest
from pathlib import Path
from unittest.mock import patch

from route_api_discovery import (
    Config,
    build_url_scope,
    collect_path_candidates,
    discover,
    extract_html_assets,
    is_http_url,
    is_scan_target_url,
    parse_input_urls,
)


class InputUrlValidationTests(unittest.TestCase):
    def test_parse_input_urls_allows_loopback_and_private_hosts(self) -> None:
        urls = parse_input_urls(
            "http://127.0.0.1:3000\n"
            "http://192.168.0.10:8080\n"
            "http://localhost:3000\n"
        )

        self.assertEqual(
            urls,
            [
                "http://127.0.0.1:3000",
                "http://192.168.0.10:8080",
                "http://localhost:3000",
            ],
        )

    def test_discovered_url_validation_still_blocks_non_public_hosts_by_default(self) -> None:
        self.assertFalse(is_http_url("http://127.0.0.1:3000"))
        self.assertFalse(is_http_url("http://192.168.0.10:8080"))
        self.assertFalse(is_http_url("http://localhost:3000"))
        self.assertTrue(is_scan_target_url("http://127.0.0.1:3000"))

    def test_extract_html_assets_keeps_loopback_script_sources(self) -> None:
        scope = build_url_scope("http://127.0.0.1:3000")

        script_urls, inline_scripts = extract_html_assets(
            '<script src="/static/app.js"></script><script>console.log("ok")</script>',
            "http://127.0.0.1:3000",
            scope,
        )

        self.assertEqual(script_urls, ["http://127.0.0.1:3000/static/app.js"])
        self.assertEqual(inline_scripts, ['console.log("ok")'])

    def test_collect_path_candidates_keeps_loopback_relative_paths(self) -> None:
        scope = build_url_scope("http://127.0.0.1:3000")
        page_bucket = {}
        api_bucket = {}

        collect_path_candidates(
            '"/dashboard" "/api/users"',
            "http://127.0.0.1:3000",
            "html:http://127.0.0.1:3000",
            scope,
            page_bucket,
            api_bucket,
        )

        self.assertIn("http://127.0.0.1:3000/dashboard", page_bucket)
        self.assertEqual(page_bucket["http://127.0.0.1:3000/dashboard"].url, "http://127.0.0.1:3000/dashboard")
        self.assertIn("http://127.0.0.1:3000/api/users", api_bucket)
        self.assertEqual(api_bucket["http://127.0.0.1:3000/api/users"].url, "http://127.0.0.1:3000/api/users")

    def test_collect_path_candidates_rejects_other_private_hosts_outside_scope(self) -> None:
        scope = build_url_scope("http://127.0.0.1:3000")
        page_bucket = {}
        api_bucket = {}

        collect_path_candidates(
            '"http://192.168.0.10:8080/admin" "http://localhost:3000/api/users"',
            "http://127.0.0.1:3000",
            "html:http://127.0.0.1:3000",
            scope,
            page_bucket,
            api_bucket,
        )

        self.assertEqual(page_bucket, {})
        self.assertEqual(api_bucket, {})

    def test_discover_accepts_loopback_root_target(self) -> None:
        config = Config(
            url="http://127.0.0.1:3000",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        stub_result = {
            "input_url": "http://127.0.0.1:3000",
            "scanned_at": "2026-04-24T12:00:00+09:00",
            "origin": "http://127.0.0.1:3000",
            "probe_skipped": False,
            "max_js_files": 1,
            "max_depth": 0,
            "max_workers": 1,
            "request_delay": 0.0,
            "proxy_url": "",
            "js_output_dir": "",
            "js_files": [],
            "js_discovered_urls": [],
            "accessible_pages": [],
            "accessible_apis": [],
            "all_pages": [],
            "all_apis": [],
            "hardcoded_findings": [],
            "hardcoded_summary": {},
            "sensitive_findings": [],
            "sensitive_summary": {},
            "summary": {
                "js_discovered": 0,
                "js_fetched": 0,
                "js_saved": 0,
                "page_count": 0,
                "api_count": 0,
            },
        }

        with patch("route_api_discovery._discover_once", return_value=stub_result) as mocked_discover_once:
            result = discover(config)

        self.assertEqual(result["input_url"], "http://127.0.0.1:3000")
        self.assertEqual(result["recursive_scanned_targets"], ["http://127.0.0.1:3000"])
        mocked_discover_once.assert_called_once()
        self.assertEqual(mocked_discover_once.call_args.args[1], "http://127.0.0.1:3000")


if __name__ == "__main__":
    unittest.main()
