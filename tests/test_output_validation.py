import unittest
import zipfile
from pathlib import Path

from route_api_discovery import Config, derive_export_output_paths, save_export_bundle, save_result, validate_config, validate_output_path


class OutputValidationTests(unittest.TestCase):
    def test_validate_output_path_allows_json_xlsx_html_and_no_suffix(self) -> None:
        for output in (
            Path("result"),
            Path("result.json"),
            Path("result.xlsx"),
            Path("result.html"),
            Path("RESULT.JSON"),
            Path("RESULT.HTML"),
        ):
            with self.subTest(output=output):
                validate_output_path(output)

    def test_validate_output_path_rejects_unsupported_suffix(self) -> None:
        with self.assertRaisesRegex(ValueError, "지원하지 않는 출력 형식"):
            validate_output_path(Path("result.txt"))

    def test_validate_config_rejects_unsupported_suffix_before_scan(self) -> None:
        config = Config(
            url="https://example.com",
            max_js_files=10,
            max_depth=2,
            timeout=5.0,
            output=Path("result.txt"),
            skip_probe=False,
        )
        with self.assertRaisesRegex(ValueError, "지원하지 않는 출력 형식"):
            validate_config(config)

    def test_save_result_still_supports_extensionless_json_output(self) -> None:
        output = Path("tests_tmp_output")
        try:
            saved_path = save_result(output, {"ok": True})
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_text(encoding="utf-8"), '{\n  "ok": true\n}')
        finally:
            if output.exists():
                output.unlink()

    def test_save_result_supports_html_output(self) -> None:
        output = Path("tests_tmp_output.html")
        try:
            saved_path = save_result(
                output,
                {
                    "summary": {
                        "js_fetched": 0,
                        "page_count": 0,
                        "api_count": 0,
                        "hardcoded_total": 1,
                        "hardcoded_high_or_above": 1,
                        "hardcoded_pii_count": 1,
                        "hardcoded_secret_count": 0,
                    },
                    "hardcoded_findings": [
                        {
                            "category": "email",
                            "field_name": "email",
                            "value": "admin@company.co.kr",
                            "masked_value": "admin@company.co.kr",
                            "normalized_value": "admin@company.co.kr",
                            "source_type": "html",
                            "source_url": "https://example.com",
                            "source_label": "html:https://example.com",
                            "line": 1,
                            "column": 1,
                            "context": "email = 'admin@company.co.kr'",
                            "confidence": 0.95,
                            "severity": "high",
                            "matched_by": "regex.email",
                        }
                    ],
                    "js_files": [],
                    "all_pages": [],
                    "all_apis": [],
                    "accessible_pages": [],
                    "accessible_apis": [],
                    "input_url": "https://example.com",
                    "scanned_at": "2026-04-08T00:00:00+09:00",
                    "probe_skipped": False,
                    "max_workers": 1,
                    "request_delay": 0.0,
                    "recursive_enabled": False,
                    "recursive_depth": 0,
                    "recursive_total_scans": 1,
                    "recursive_discovered_targets": [],
                    "recursive_failed_targets": [],
                    "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
                },
            )
            self.assertEqual(saved_path, output.resolve())
            html_text = saved_path.read_text(encoding="utf-8")
            self.assertIn("Route API Discovery Report", html_text)
            self.assertIn("admin@company.co.kr", html_text)
            self.assertIn("report-shell", html_text)
        finally:
            if output.exists():
                output.unlink()

    def test_save_result_supports_xlsx_output(self) -> None:
        output = Path("tests_tmp_output.xlsx")
        try:
            saved_path = save_result(
                output,
                {
                    "summary": {
                        "js_fetched": 0,
                        "page_count": 0,
                        "api_count": 0,
                        "hardcoded_total": 1,
                        "hardcoded_high_or_above": 1,
                        "hardcoded_pii_count": 1,
                        "hardcoded_secret_count": 0,
                    },
                    "hardcoded_findings": [
                        {
                            "category": "email",
                            "field_name": "email",
                            "value": "admin@company.co.kr",
                            "masked_value": "admin@company.co.kr",
                            "normalized_value": "admin@company.co.kr",
                            "source_type": "html",
                            "source_url": "https://example.com",
                            "source_label": "html:https://example.com",
                            "line": 1,
                            "column": 1,
                            "context": "email = 'admin@company.co.kr'",
                            "confidence": 0.95,
                            "severity": "high",
                            "matched_by": "regex.email",
                        }
                    ],
                    "js_files": [],
                    "all_pages": [],
                    "all_apis": [],
                    "accessible_pages": [],
                    "accessible_apis": [],
                    "input_url": "https://example.com",
                    "scanned_at": "2026-04-08T00:00:00+09:00",
                    "probe_skipped": False,
                    "max_workers": 1,
                    "request_delay": 0.0,
                    "recursive_enabled": False,
                    "recursive_depth": 0,
                    "recursive_total_scans": 1,
                    "recursive_discovered_targets": [],
                    "recursive_failed_targets": [],
                    "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
                },
            )
            self.assertTrue(saved_path.exists())
            with zipfile.ZipFile(saved_path) as workbook:
                self.assertIn("[Content_Types].xml", workbook.namelist())
                self.assertIn("xl/workbook.xml", workbook.namelist())
                workbook_xml = workbook.read("xl/workbook.xml").decode("utf-8")
                self.assertIn("민감정보", workbook_xml)
                styles_xml = workbook.read("xl/styles.xml").decode("utf-8")
                self.assertIn('<cellXfs count="6">', styles_xml)
        finally:
            if output.exists():
                output.unlink()

    def test_save_result_supports_xlsx_output_with_sensitive_alias_fields(self) -> None:
        output = Path("tests_tmp_output_sensitive.xlsx")
        try:
            saved_path = save_result(
                output,
                {
                    "summary": {
                        "js_fetched": 0,
                        "page_count": 0,
                        "api_count": 0,
                        "sensitive_total": 1,
                        "sensitive_high_or_above": 1,
                        "sensitive_pii_count": 1,
                        "sensitive_secret_count": 0,
                    },
                    "sensitive_findings": [
                        {
                            "category": "email",
                            "field_name": "email",
                            "value": "admin@company.co.kr",
                            "masked_value": "admin@company.co.kr",
                            "normalized_value": "admin@company.co.kr",
                            "source_type": "html",
                            "source_url": "https://example.com",
                            "source_label": "html:https://example.com",
                            "line": 1,
                            "column": 1,
                            "context": "email = 'admin@company.co.kr'",
                            "confidence": 0.95,
                            "severity": "high",
                            "matched_by": "regex.email",
                        }
                    ],
                    "hardcoded_findings": [],
                    "js_files": [],
                    "all_pages": [],
                    "all_apis": [],
                    "accessible_pages": [],
                    "accessible_apis": [],
                    "input_url": "https://example.com",
                    "scanned_at": "2026-04-08T00:00:00+09:00",
                    "probe_skipped": False,
                    "max_workers": 1,
                    "request_delay": 0.0,
                    "recursive_enabled": False,
                    "recursive_depth": 0,
                    "recursive_total_scans": 1,
                    "recursive_discovered_targets": [],
                    "recursive_failed_targets": [],
                    "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
                },
            )
            self.assertTrue(saved_path.exists())
            with zipfile.ZipFile(saved_path) as workbook:
                self.assertIn("[Content_Types].xml", workbook.namelist())
                self.assertIn("xl/workbook.xml", workbook.namelist())
                sensitive_xml = workbook.read("xl/worksheets/sheet5.xml").decode("utf-8")
                self.assertIn("admin@company.co.kr", sensitive_xml)
                self.assertIn("<cols>", sensitive_xml)
        finally:
            if output.exists():
                output.unlink()

    def test_save_export_bundle_writes_xlsx_and_html_together(self) -> None:
        output = Path("tests_tmp_bundle")
        xlsx_output = output.with_suffix(".xlsx")
        html_output = output.with_suffix(".html")
        payload = {
            "summary": {
                "js_fetched": 0,
                "page_count": 0,
                "api_count": 0,
                "sensitive_total": 1,
                "sensitive_high_or_above": 1,
                "sensitive_pii_count": 1,
                "sensitive_secret_count": 0,
            },
            "sensitive_findings": [
                {
                    "category": "email",
                    "field_name": "email",
                    "value": "admin@company.co.kr",
                    "masked_value": "admin@company.co.kr",
                    "normalized_value": "admin@company.co.kr",
                    "source_type": "html",
                    "source_url": "https://example.com",
                    "source_label": "html:https://example.com",
                    "line": 1,
                    "column": 1,
                    "context": "email = 'admin@company.co.kr'",
                    "confidence": 0.95,
                    "severity": "high",
                    "matched_by": "regex.email",
                }
            ],
            "hardcoded_findings": [],
            "js_files": [],
            "all_pages": [],
            "all_apis": [],
            "accessible_pages": [],
            "accessible_apis": [],
            "input_url": "https://example.com",
            "scanned_at": "2026-04-08T00:00:00+09:00",
            "probe_skipped": False,
            "max_workers": 1,
            "request_delay": 0.0,
            "recursive_enabled": False,
            "recursive_depth": 0,
            "recursive_total_scans": 1,
            "recursive_discovered_targets": [],
            "recursive_failed_targets": [],
            "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
        }
        try:
            saved_xlsx, saved_html = save_export_bundle(output, payload)
            self.assertEqual(saved_xlsx, xlsx_output.resolve())
            self.assertEqual(saved_html, html_output.resolve())
            self.assertTrue(saved_xlsx.exists())
            self.assertTrue(saved_html.exists())
            html_text = saved_html.read_text(encoding="utf-8")
            self.assertIn("Route API Discovery Report", html_text)
            self.assertIn("admin@company.co.kr", html_text)
            self.assertIn("report-shell", html_text)
            self.assertIn("metric-grid", html_text)
            self.assertIn("quick-nav", html_text)
            self.assertIn("detail-accordion", html_text)
        finally:
            if xlsx_output.exists():
                xlsx_output.unlink()
            if html_output.exists():
                html_output.unlink()

    def test_derive_export_output_paths_accepts_xlsx_html_or_no_suffix(self) -> None:
        self.assertEqual(derive_export_output_paths(Path("report")), (Path("report.xlsx"), Path("report.html")))
        self.assertEqual(derive_export_output_paths(Path("report.xlsx")), (Path("report.xlsx"), Path("report.html")))
        self.assertEqual(derive_export_output_paths(Path("report.html")), (Path("report.xlsx"), Path("report.html")))


if __name__ == "__main__":
    unittest.main()
