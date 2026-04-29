import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from route_api_discovery import (
    Candidate,
    Config,
    ExecutionContext,
    RequestThrottle,
    ScanCancelled,
    build_result_rows,
    discover_many,
    ensure_not_cancelled,
)


def _minimal_result(url: str) -> dict:
    return {
        "input_url": url,
        "scanned_at": "2026-04-08T00:00:00+09:00",
        "origin": "https://example.com",
        "probe_skipped": False,
        "max_js_files": 1,
        "max_depth": 0,
        "max_workers": 1,
        "request_delay": 0.0,
        "recursive_enabled": False,
        "recursive_depth": 0,
        "recursive_scanned_targets": [url],
        "recursive_discovered_targets": [],
        "recursive_total_scans": 1,
        "recursive_failed_targets": [],
        "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
        "js_files": [],
        "accessible_pages": [],
        "accessible_apis": [],
        "all_pages": [],
        "all_apis": [],
        "summary": {
            "js_discovered": 0,
            "js_fetched": 0,
            "page_count": 0,
            "api_count": 0,
        },
    }


class ScanCancellationTests(unittest.TestCase):
    def test_ensure_not_cancelled_raises_when_cancel_requested(self) -> None:
        execution = ExecutionContext(max_workers=1, request_throttle=RequestThrottle())
        execution.cancel_event.set()

        with self.assertRaisesRegex(ScanCancelled, "사용자 요청으로 스캔을 중지했습니다."):
            ensure_not_cancelled(execution)

    def test_build_result_rows_stops_before_processing_candidates(self) -> None:
        execution = ExecutionContext(max_workers=1, request_throttle=RequestThrottle())
        execution.cancel_event.set()
        bucket = {
            "/alpha": Candidate(
                url="https://example.com/alpha",
                path="/alpha",
                kind="page",
                sources={"test"},
            )
        }

        with self.assertRaisesRegex(ScanCancelled, "사용자 요청으로 스캔을 중지했습니다."):
            build_result_rows(bucket, kind="page", timeout=1.0, skip_probe=False, execution=execution)

    def test_discover_many_stops_before_scanning_next_url(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        execution = ExecutionContext(max_workers=1, request_throttle=RequestThrottle(), cancel_event=threading.Event())
        scanned_urls: list[str] = []

        def fake_discover(per_url_config: Config, progress=None, execution=None):
            scanned_urls.append(per_url_config.url)
            execution.cancel_event.set()
            return _minimal_result(per_url_config.url)

        with patch("route_api_discovery.discover", side_effect=fake_discover):
            with self.assertRaisesRegex(ScanCancelled, "사용자 요청으로 스캔을 중지했습니다."):
                discover_many(
                    config,
                    ["https://example.com", "https://example.org"],
                    execution=execution,
                )

        self.assertEqual(scanned_urls, ["https://example.com"])

    def test_discover_many_propagates_scan_cancelled_from_discover(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=1,
            max_depth=0,
            timeout=1.0,
            output=Path("discovery-result.json"),
            skip_probe=False,
        )
        execution = ExecutionContext(max_workers=1, request_throttle=RequestThrottle(), cancel_event=threading.Event())

        def fake_discover(per_url_config: Config, progress=None, execution=None):
            raise ScanCancelled("cancelled")

        with patch("route_api_discovery.discover", side_effect=fake_discover):
            with self.assertRaisesRegex(ScanCancelled, "cancelled"):
                discover_many(
                    config,
                    ["https://example.com", "https://example.org"],
                    execution=execution,
                )


if __name__ == "__main__":
    unittest.main()
