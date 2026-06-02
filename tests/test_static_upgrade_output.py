import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from route_api_discovery import parse_args, build_config


class ConfigFlagTests(unittest.TestCase):
    def test_defaults_enable_well_known_and_low_min_confidence(self):
        args = parse_args(["https://example.com"])
        config = build_config(args)
        self.assertTrue(config.scan_well_known)
        self.assertEqual(config.min_confidence, "low")

    def test_no_scan_well_known_flag(self):
        args = parse_args(["https://example.com", "--no-scan-well-known"])
        config = build_config(args)
        self.assertFalse(config.scan_well_known)

    def test_min_confidence_flag(self):
        args = parse_args(["https://example.com", "--min-confidence", "high"])
        config = build_config(args)
        self.assertEqual(config.min_confidence, "high")


from route_api_discovery import build_result_row, Candidate, ProbeResult


class ResultRowConfidenceTests(unittest.TestCase):
    def test_result_row_includes_confidence_and_detectors(self):
        candidate = Candidate(
            url="https://example.com/api/users",
            path="/api/users",
            kind="api",
            confidence="high",
        )
        candidate.detectors.add("fetch")
        row = build_result_row(candidate, kind="api", timeout=1.0, skip_probe=True)
        self.assertEqual(row["confidence"], "high")
        self.assertIn("fetch", row["detectors"])


from route_api_discovery import filter_rows_by_min_confidence


class MinConfidenceFilterTests(unittest.TestCase):
    def test_filters_below_threshold(self):
        rows = [
            {"url": "a", "confidence": "low"},
            {"url": "b", "confidence": "medium"},
            {"url": "c", "confidence": "high"},
        ]
        result = filter_rows_by_min_confidence(rows, "medium")
        urls = {r["url"] for r in result}
        self.assertEqual(urls, {"b", "c"})

    def test_low_threshold_keeps_all(self):
        rows = [{"url": "a", "confidence": "low"}, {"url": "b", "confidence": "high"}]
        result = filter_rows_by_min_confidence(rows, "low")
        self.assertEqual(len(result), 2)


from route_api_discovery import build_result_sheet_rows


class SheetConfidenceColumnTests(unittest.TestCase):
    def test_header_includes_confidence(self):
        rows = build_result_sheet_rows([])
        header = rows[0]
        self.assertIn("신뢰도", header)

    def test_row_includes_confidence_value(self):
        rows = build_result_sheet_rows([
            {
                "status_code": 200,
                "accessible": True,
                "probe_method": "GET",
                "path": "/api/users",
                "sources": ["html:x"],
                "url": "https://example.com/api/users",
                "confidence": "high",
            }
        ])
        data_row = rows[1]
        self.assertIn("high", data_row)


class GuiRowConfidenceTests(unittest.TestCase):
    def test_api_row_carries_confidence(self):
        import route_api_discovery_ctk as ctk
        record = {
            "all_apis": [
                {
                    "url": "https://example.com/api/users",
                    "path": "/api/users",
                    "confidence": "high",
                    "accessible": True,
                    "status_code": 200,
                }
            ],
            "all_pages": [],
            "js_files": [],
        }
        app = ctk.CtkDiscoveryApp.__new__(ctk.CtkDiscoveryApp)
        rows = ctk.CtkDiscoveryApp._build_rows(app, record)
        api_rows = [r for r in rows if r["kind"] == "api"]
        self.assertTrue(any(r.get("confidence") == "high" for r in api_rows))


if __name__ == "__main__":
    unittest.main()
