import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt, QThread
from PySide6.QtWidgets import QApplication

from route_api_discovery import CANCEL_MESSAGE, Config, build_summary_text
from route_api_discovery_qt import DiscoveryWindow, ScanRequest, ScanWorker


def _sample_result() -> dict:
    return {
        "input_url": "https://example.com",
        "scanned_at": "2026-04-08T13:00:00+09:00",
        "status": "success",
        "error": "",
        "summary": {
            "js_fetched": 2,
            "page_count": 3,
            "api_count": 1,
        },
        "probe_skipped": False,
        "include_subdomains": True,
        "excluded_subdomains": ["cdn.example.com"],
        "max_workers": 1,
        "request_delay": 0.0,
        "recursive_enabled": True,
        "recursive_depth": 1,
        "recursive_total_scans": 2,
        "recursive_discovered_targets": ["https://example.com/about"],
        "recursive_failed_targets": [],
        "recursive_dedupe": {"js": 0, "pages": 1, "apis": 0, "targets": 0},
        "accessible_pages": [
            {"status_code": 200, "path": "/about", "url": "https://example.com/about"},
        ],
        "accessible_apis": [
            {"status_code": 200, "path": "/api/users", "url": "https://example.com/api/users"},
        ],
        "js_files": [],
        "all_pages": [],
        "all_apis": [],
    }


def _sample_batch_result() -> dict:
    return {
        "input_urls": ["https://example.com"],
        "success_count": 1,
        "failed_count": 0,
        "results": [_sample_result()],
    }


def _sample_config() -> Config:
    return Config(
        url="https://example.com",
        max_js_files=5,
        max_depth=2,
        timeout=1.0,
        output=Path("discovery-result.json"),
        skip_probe=False,
    )


def _sample_multi_batch_result() -> dict:
    first = _sample_result()
    second = _sample_result()
    second["input_url"] = "https://example.com/admin"
    second["accessible_pages"] = [{"status_code": 200, "path": "/admin", "url": "https://example.com/admin"}]
    return {
        "input_urls": ["https://example.com", "https://example.com/admin"],
        "success_count": 2,
        "failed_count": 0,
        "results": [first, second],
    }


class GuiLanguageOptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        settings = QSettings("RouteApiDiscovery", "RouteApiDiscovery")
        settings.clear()

    def test_build_summary_text_supports_english(self) -> None:
        text = build_summary_text(_sample_result(), Path("discovery-result.json"), language="en")

        self.assertIn("=== Summary ===", text)
        self.assertIn("Input URL: https://example.com", text)
        self.assertIn("Accessible pages:", text)
        self.assertIn("Accessible APIs:", text)

    def test_language_option_switches_gui_labels_to_english(self) -> None:
        window = DiscoveryWindow()
        try:
            self.assertEqual(window.language_label.text(), "언어")
            self.assertEqual(window.language_combo.currentText(), "한국어")

            window.language_combo.setCurrentIndex(1)

            self.assertEqual(window.language_label.text(), "Language")
            self.assertEqual(window.language_combo.currentText(), "English")
            self.assertEqual(window.run_button.text(), "Run")
            self.assertEqual(window.result_selector_label.text(), "Result")
            self.assertEqual(window.tab_widget.tabText(0), "Summary")
            self.assertEqual(window.tab_widget.tabText(1), "Sensitive")
            self.assertEqual(window.js_bundle.filter_label.text(), "Filter")
            self.assertEqual(window.include_subdomains_check.text(), "Include subdomains")
            self.assertEqual(window.excluded_subdomains_label.text(), "Excluded subdomains")
        finally:
            window.close()

    def test_sensitive_tab_metrics_and_filters_localize_and_update(self) -> None:
        window = DiscoveryWindow()
        try:
            window.language_combo.setCurrentIndex(1)
            self.assertEqual(window.card_sensitive_total_title.text(), "Sensitive total")
            self.assertEqual(window.card_sensitive_high_title.text(), "Sensitive high+")
            self.assertEqual(window.sensitive_bundle.quick_check.text(), "High only")
            self.assertEqual(window.sensitive_type_label.text(), "Type")

            result = _sample_result()
            result["summary"]["sensitive_total"] = 2
            result["summary"]["sensitive_high_or_above"] = 1
            result["sensitive_findings"] = [
                {
                    "type": "email",
                    "value": "admin@example.com",
                    "masked_value": "a***@example.com",
                    "confidence": 0.93,
                    "severity": "high",
                    "source_type": "js",
                    "source_url": "https://example.com/app.js",
                    "location": {"line": 10, "column": 5},
                },
                {
                    "type": "phone",
                    "value": "010-1234-5678",
                    "masked_value": "010-****-5678",
                    "confidence": 0.78,
                    "severity": "low",
                    "source_type": "page",
                    "source_url": "https://example.com/login",
                    "location_label": "line 33, col 2",
                },
            ]
            window._update_for_selected_result(result)

            self.assertEqual(window.card_sensitive_total_value.text(), "2")
            self.assertEqual(window.card_sensitive_high_value.text(), "1")
            self.assertEqual(window.sensitive_table.rowCount(), 2)
            self.assertEqual(window.sensitive_table.item(0, 1).text(), "a***@example.com")
            self.assertEqual(window.sensitive_table.item(1, 1).text(), "010-****-5678")
        finally:
            window.close()

    def test_sensitive_tab_falls_back_to_hardcoded_findings_when_sensitive_is_empty(self) -> None:
        window = DiscoveryWindow()
        try:
            result = _sample_result()
            result["summary"]["hardcoded_total"] = 1
            result["summary"]["hardcoded_high_or_above"] = 1
            result["sensitive_findings"] = []
            result["hardcoded_findings"] = [
                {
                    "category": "email",
                    "masked_value": "b***@example.com",
                    "confidence": 0.91,
                    "severity": "high",
                    "source_type": "js",
                    "source_url": "https://example.com/app.js",
                    "line": 12,
                    "column": 3,
                }
            ]

            window._update_for_selected_result(result)

            self.assertEqual(window.sensitive_table.rowCount(), 1)
            self.assertEqual(window.sensitive_table.item(0, 1).text(), "b***@example.com")
        finally:
            window.close()

    def test_scan_completion_marks_results_unsaved_until_save_button_runs(self) -> None:
        window = DiscoveryWindow()
        try:
            window.language_combo.setCurrentIndex(1)
            window._on_finished(_sample_batch_result())

            self.assertTrue(window.save_again_button.isEnabled())
            self.assertIn("Not saved", window.current_output_label.text())
            self.assertIn("Not saved", window.summary_text.toPlainText())
            saved_xlsx = str(Path("saved-output.xlsx").resolve())
            saved_html = str(Path("saved-output.html").resolve())
            window._on_save_finished((saved_xlsx, saved_html))
            self.assertIn("saved-output.xlsx", window.current_output_label.text())
            self.assertIn("saved-output.html", window.current_output_label.text())
            self.assertIn("saved-output.xlsx", window.summary_text.toPlainText())
            self.assertIn("saved-output.html", window.summary_text.toPlainText())
        finally:
            window.close()

    def test_scan_worker_cancel_message_uses_readable_korean(self) -> None:
        worker = ScanWorker(ScanRequest(urls=["https://example.com"], config=_sample_config()))
        cancelled_messages: list[str] = []
        worker.cancelled.connect(cancelled_messages.append)
        worker.cancel()

        with patch("route_api_discovery_qt.discover_many", return_value=_sample_batch_result()):
            worker.run()

        self.assertEqual(cancelled_messages, [CANCEL_MESSAGE])
        self.assertIn("사용자 요청", cancelled_messages[0])
        self.assertIn("스캔을 중지", cancelled_messages[0])
        for mojibake_marker in (chr(0xFFFD), chr(0x00C3), chr(0x00EC), chr(0x00ED), chr(0x00EB)):
            self.assertNotIn(mojibake_marker, cancelled_messages[0])

    def test_cancel_scan_state_resets_with_readable_cancel_message(self) -> None:
        class FakeWorker:
            def __init__(self) -> None:
                self.cancel_requested = False

            def cancel(self) -> None:
                self.cancel_requested = True

            def is_cancel_requested(self) -> bool:
                return self.cancel_requested

        window = DiscoveryWindow()
        try:
            window.worker = FakeWorker()
            window.worker_thread = object()

            window.cancel_scan()

            self.assertEqual(window.state_mode, "cancelling")
            self.assertEqual(window.state_chip.text(), "중지 요청 중")
            self.assertEqual(window.secondary_chip.text(), "중단 대기")
            self.assertFalse(window.stop_button.isEnabled())

            window._on_cancelled(CANCEL_MESSAGE)

            self.assertEqual(window.state_mode, "idle")
            self.assertEqual(window.left_state_hint.text(), CANCEL_MESSAGE)
            self.assertIn(CANCEL_MESSAGE, window.log_text.toPlainText())
            self.assertFalse(window.save_again_button.isEnabled())
        finally:
            window.worker = None
            window.worker_thread = None
            window.close()

    def test_save_failure_preserves_selected_result_and_retry_state(self) -> None:
        window = DiscoveryWindow()
        try:
            window.language_combo.setCurrentIndex(1)
            window._on_finished(_sample_multi_batch_result())
            window.result_selector.setCurrentIndex(1)
            self.assertIn("example.com/admin", window.summary_text.toPlainText())

            with patch("route_api_discovery_qt.QMessageBox.critical", return_value=None):
                window._on_save_failed("disk full")

            self.assertEqual(window.result_selector.currentIndex(), 1)
            self.assertEqual(window.state_mode, "error")
            self.assertTrue(window.save_again_button.isEnabled())
            self.assertIn("save failed", window.current_output_label.text())
            self.assertIn("example.com/admin", window.summary_text.toPlainText())

            window.language_combo.setCurrentIndex(0)
            self.assertEqual(window.last_save_error_message, "disk full")
            self.assertEqual(window.last_error_message.count("disk full"), 1)
        finally:
            window._cleanup_save_worker()
            window.close()

    def test_run_scan_uses_internal_output_path_even_if_default_save_name_is_invalid(self) -> None:
        window = DiscoveryWindow()
        try:
            window.default_output_path = "result.txt"
            window.url_input.setPlainText("https://example.com")
            captured: dict[str, Path] = {}

            def fake_validate(config) -> None:
                captured["output"] = config.output

            with patch("route_api_discovery_qt.validate_config", side_effect=fake_validate), patch.object(
                QThread,
                "start",
                return_value=None,
            ):
                window.run_scan()

            self.assertEqual(captured["output"], Path("discovery-result.json"))
        finally:
            window._cleanup_worker()
            window.close()

    def test_scan_inputs_lock_while_running_and_restore_when_ready(self) -> None:
        window = DiscoveryWindow()
        try:
            window.recursive_scan_check.setChecked(True)

            window._set_running_state()

            self.assertFalse(window.url_input.isEnabled())
            self.assertFalse(window.header_input.isEnabled())
            self.assertFalse(window.max_js_spin.isEnabled())
            self.assertFalse(window.recursive_depth_spin.isEnabled())
            self.assertTrue(window.stop_button.isEnabled())

            window._set_result_ready_state("done")

            self.assertTrue(window.url_input.isEnabled())
            self.assertTrue(window.header_input.isEnabled())
            self.assertTrue(window.max_js_spin.isEnabled())
            self.assertTrue(window.recursive_depth_spin.isEnabled())
            self.assertFalse(window.stop_button.isEnabled())
        finally:
            window.close()

    def test_table_cells_keep_full_tooltips_and_numeric_sorting(self) -> None:
        window = DiscoveryWindow()
        try:
            window._populate_table(
                window.api_table,
                [
                    ("404", "No", "GET", "/missing", "source", "https://example.com/missing"),
                    ("200", "Yes", "GET", "/ok", "source", "https://example.com/ok"),
                ],
            )

            self.assertEqual(window.api_table.item(0, 5).toolTip(), "https://example.com/missing")
            window.api_table.sortItems(0, Qt.SortOrder.AscendingOrder)
            self.assertEqual(window.api_table.item(0, 0).text(), "200")
        finally:
            window.close()

    def test_get_save_output_path_normalizes_bundle_base_name(self) -> None:
        window = DiscoveryWindow()
        try:
            with patch("route_api_discovery_qt.QFileDialog.getSaveFileName", return_value=("C:\\temp\\bundle.xlsx", "")):
                output_path = window._get_save_output_path()

            self.assertEqual(output_path, Path("C:/temp/bundle"))
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
