#!/usr/bin/env python3
"""PySide6 GUI for route_api_discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import List, Optional, Tuple

from PySide6.QtCore import QObject, QSettings, Qt, QThread, Signal
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QDoubleSpinBox,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from route_api_discovery import (
    CANCEL_MESSAGE,
    Config,
    ScanCancelled,
    build_batch_summary_text,
    build_execution_context,
    build_summary_text,
    discover_many,
    filter_table_rows,
    format_export_output_label,
    parse_hostname_filters,
    parse_header_lines,
    parse_input_urls,
    save_export_bundle,
    validate_config,
)

UI_TEXTS = {
    "ko": {
        "window_title": "Route API Discovery - Precision Workbench",
        "app_title": "Route API Discovery",
        "app_subtitle": "Precision Workbench",
        "cell_detail_title": "셀 상세",
        "copy": "복사",
        "close": "닫기",
        "close_scan_request_title": "중지 요청",
        "close_scan_request_body": "창을 닫기 전에 스캔 중지를 요청했습니다.\n중단이 완료되면 다시 닫아 주세요.",
        "close_scan_wait_title": "중단 대기",
        "close_scan_wait_body": "스캔 중지가 진행 중입니다.\n중단이 완료되면 다시 닫아 주세요.",
        "target_url": "대상 URL",
        "run": "실행",
        "stop": "정지",
        "settings": "설정",
        "url_placeholder": "한 줄에 하나씩 URL 입력\n예) https://example.com",
        "headers_placeholder": "Header-Name: value",
        "output_file": "출력 파일",
        "output_placeholder": "결과 파일(.json/.xlsx, 확장자 없으면 JSON)",
        "output_hint": "Excel + HTML 리포트 번들을 저장할 기준 이름을 지정합니다.",
        "browse": "찾아보기",
        "request_headers": "요청 헤더",
        "options": "탐색 옵션",
        "timeout_suffix": " 초",
        "recursive_scan": "재귀탐색 사용",
        "include_subdomains": "서브도메인 포함",
        "excluded_subdomains": "제외할 서브도메인",
        "excluded_subdomains_placeholder": "예: cdn.example.com, static.example.com",
        "skip_probe": "프로브 생략",
        "verify_ssl": "SSL 인증서 검증",
        "max_js": "JS 최대 개수",
        "max_depth": "최대 깊이",
        "timeout": "타임아웃",
        "recursive_depth": "재귀 단계",
        "max_workers": "동시 요청 수",
        "request_delay": "요청 딜레이",
        "proxy": "프록시",
        "proxy_placeholder": "예: http://127.0.0.1:8080",
        "js_output_dir": "JS 저장 폴더",
        "js_output_dir_placeholder": "비워두면 JS 본문을 저장하지 않습니다",
        "choose_js_output_dir": "JS 저장 폴더 선택",
        "language": "언어",
        "language_ko": "한국어",
        "language_en": "영어",
        "execution_status": "실행 상태",
        "idle_hint": "대상 URL을 입력하고 실행을 눌러주세요.",
        "save_output_file": "출력 파일 선택",
        "state_idle": "준비됨",
        "state_running": "실행 중",
        "state_cancelling": "중지 요청 중",
        "state_ready": "완료",
        "state_error": "오류",
        "secondary_no_results": "결과 없음",
        "secondary_scanning": "탐색 진행",
        "secondary_stopping": "중단 대기",
        "secondary_ready": "결과 준비됨",
        "secondary_failed": "실행 실패",
        "secondary_selected_success": "선택 결과: 성공",
        "secondary_selected_failed": "선택 결과: 실패",
        "results": "결과",
        "result_selector": "결과 선택",
        "dark_mode": "다크 모드",
        "current_target": "현재 대상: {value}",
        "current_output": "출력 경로: {value}",
        "metric_js": "JS 파일 수",
        "metric_page": "페이지 수",
        "metric_api": "API 수",
        "metric_recursive": "재귀 스캔 대상 수",
        "metric_sensitive_total": "민감정보 총계",
        "metric_sensitive_high": "민감정보 high+",
        "empty_state": "아직 결과가 없습니다.\n좌측에서 대상 URL을 입력하고 실행하세요.",
        "running_state": "탐색 실행 중입니다...\n하단 로그 패널에서 진행 상황을 확인하세요.",
        "tab_summary": "요약",
        "tab_sensitive": "민감정보",
        "tab_js": "JS 파일",
        "tab_page": "페이지",
        "tab_api": "API",
        "tab_log": "로그",
        "clear_log": "지우기",
        "save_log": "로그 저장",
        "header_depth": "깊이",
        "header_status": "상태",
        "header_success": "성공",
        "header_length": "길이",
        "header_saved_path": "저장 경로",
        "header_save_error": "저장 오류",
        "header_error": "오류",
        "header_url": "URL",
        "header_accessible": "접근 가능",
        "header_method": "방법",
        "header_path": "경로",
        "header_source": "출처",
        "header_sensitive_type": "유형",
        "header_masked_value": "값",
        "header_confidence": "신뢰도",
        "header_severity": "심각도",
        "header_location": "위치",
        "quick_success_only": "성공만",
        "quick_accessible_only": "접근 가능만",
        "quick_high_only": "High only",
        "status_200_only": "상태 200만",
        "filter": "필터",
        "filter_type": "유형",
        "all": "전체",
        "sensitive_type_all": "전체",
        "sensitive_type_email": "email",
        "sensitive_type_phone": "phone",
        "sensitive_type_name": "name",
        "sensitive_type_account": "account",
        "sensitive_type_credential": "credential",
        "sensitive_type_token": "token",
        "sensitive_type_user_id": "user_id",
        "sensitive_type_other": "other",
        "search_placeholder": "검색어 입력",
        "reset": "초기화",
        "count_label": "표시 {visible} / 전체 {total}",
        "save_dialog_title": "내보내기 기준 이름 선택",
        "save_dialog_filter": "내보내기 기준 이름 (*.xlsx *.html);;모든 파일 (*)",
        "save_log_title": "로그 파일 저장",
        "save_log_filter": "로그 파일 (*.log *.txt);;모든 파일 (*)",
        "scan_in_progress_title": "진행 중",
        "scan_in_progress_body": "이미 스캔이 실행 중입니다.",
        "input_error_title": "입력 오류",
        "security_warning_title": "보안 경고",
        "security_warning_body": "SSL 인증서 검증이 비활성화되어 있습니다.\n신뢰할 수 있는 대상에만 사용해 주세요.",
        "log_ssl_warning": "[경고] SSL 인증서 검증이 비활성화되었습니다.",
        "no_scan_title": "정지",
        "no_scan_body": "현재 실행 중인 스캔이 없습니다.",
        "log_cancel_requested": "[중지 요청] 현재 요청이 끝나면 스캔을 중지합니다.",
        "log_save_completed": "저장 완료: {path} (Excel + HTML)",
        "scan_complete_message": "{count}개 URL 스캔 완료 (성공 {success}, 실패 {failed})",
        "log_error": "[오류] {message}",
        "execution_error_title": "실행 오류",
        "log_save_error": "[저장 오류] {message}",
        "output_save_failed": "저장 실패",
        "save_failed_state": "스캔은 완료됐지만 결과 저장에 실패했습니다: {message}",
        "save_failed_hint": "{count}개 URL 스캔 완료 (성공 {success}, 실패 {failed}) / 저장 실패",
        "save_error_title": "저장 오류",
        "save_error_body": "스캔은 완료됐지만 결과 저장에 실패했습니다.\n{message}",
        "log_cancelled": "[중지됨] {message}",
        "running_hint": "탐색이 진행 중입니다. 우측 하단 로그 패널에서 진행 상황을 확인할 수 있습니다.",
        "cancelling_hint": "현재 요청이 끝나는 대로 스캔을 중지합니다. 잠시만 기다려 주세요.",
        "result_selector_item": "{index}. [{status}] {url}",
        "yes": "예",
        "no": "아니오",
        "skipped": "생략",
        "save_results": "결과 저장",
        "no_results_title": "저장 불가",
        "no_results_body": "저장할 결과가 없습니다. 먼저 스캔을 실행해 주세요.",
        "output_not_saved": "미저장",
        "state_saving": "저장 중",
        "secondary_saving": "저장 중",
        "save_in_progress_title": "저장 중",
        "save_in_progress_body": "결과를 저장하고 있습니다. 완료된 뒤 다시 시도해 주세요.",
        "saving_hint": "결과를 저장하고 있습니다. 잠시만 기다려 주세요.",
        "run_tooltip": "입력한 URL로 스캔을 시작합니다.",
        "stop_tooltip": "현재 진행 중인 스캔 중지를 요청합니다.",
        "save_results_tooltip": "현재 결과를 Excel과 HTML 파일로 저장합니다.",
        "filter_tooltip": "테이블에서 표시할 행을 좁힙니다.",
        "table_tooltip": "셀을 더블클릭하면 전체 내용을 복사하고 자세히 볼 수 있습니다.",
    },
    "en": {
        "window_title": "Route API Discovery - Precision Workbench",
        "app_title": "Route API Discovery",
        "app_subtitle": "Precision Workbench",
        "cell_detail_title": "Cell Details",
        "copy": "Copy",
        "close": "Close",
        "close_scan_request_title": "Stop Requested",
        "close_scan_request_body": "A stop request was sent before closing the window.\nPlease close it again after the scan stops.",
        "close_scan_wait_title": "Stopping",
        "close_scan_wait_body": "The scan is stopping.\nPlease close the window again after it finishes.",
        "target_url": "Target URL",
        "run": "Run",
        "stop": "Stop",
        "settings": "Settings",
        "url_placeholder": "Enter one URL per line\nExample) https://example.com",
        "headers_placeholder": "Header-Name: value",
        "output_file": "Output file",
        "output_placeholder": "Result file (.json/.xlsx, JSON if no extension)",
        "output_hint": "Choose a base filename for the Excel + HTML export bundle.",
        "browse": "Browse",
        "request_headers": "Request headers",
        "options": "Scan options",
        "timeout_suffix": " sec",
        "recursive_scan": "Enable recursive scan",
        "include_subdomains": "Include subdomains",
        "excluded_subdomains": "Excluded subdomains",
        "excluded_subdomains_placeholder": "Example: cdn.example.com, static.example.com",
        "skip_probe": "Skip probe",
        "verify_ssl": "Verify SSL certificate",
        "max_js": "Max JS files",
        "max_depth": "Max depth",
        "timeout": "Timeout",
        "recursive_depth": "Recursive depth",
        "max_workers": "Concurrent requests",
        "request_delay": "Request delay",
        "proxy": "Proxy",
        "proxy_placeholder": "Example: http://127.0.0.1:8080",
        "js_output_dir": "JS output folder",
        "js_output_dir_placeholder": "Leave blank to skip saving JS bodies",
        "choose_js_output_dir": "Choose JS output folder",
        "language": "Language",
        "language_ko": "Korean",
        "language_en": "English",
        "execution_status": "Execution status",
        "idle_hint": "Enter a target URL and click Run.",
        "save_output_file": "Choose output file",
        "state_idle": "Ready",
        "state_running": "Running",
        "state_cancelling": "Stopping",
        "state_ready": "Done",
        "state_error": "Error",
        "secondary_no_results": "No results",
        "secondary_scanning": "Scanning",
        "secondary_stopping": "Waiting to stop",
        "secondary_ready": "Results ready",
        "secondary_failed": "Run failed",
        "secondary_selected_success": "Selected result: Success",
        "secondary_selected_failed": "Selected result: Failed",
        "results": "Results",
        "result_selector": "Result",
        "dark_mode": "Dark mode",
        "current_target": "Current target: {value}",
        "current_output": "Output path: {value}",
        "metric_js": "JS files",
        "metric_page": "Pages",
        "metric_api": "APIs",
        "metric_recursive": "Recursive targets",
        "metric_sensitive_total": "Sensitive total",
        "metric_sensitive_high": "Sensitive high+",
        "empty_state": "No results yet.\nEnter a target URL on the left and run the scan.",
        "running_state": "Scan is running...\nCheck the log panel below for progress.",
        "tab_summary": "Summary",
        "tab_sensitive": "Sensitive",
        "tab_js": "JS Files",
        "tab_page": "Pages",
        "tab_api": "APIs",
        "tab_log": "Log",
        "clear_log": "Clear",
        "save_log": "Save Log",
        "header_depth": "Depth",
        "header_status": "Status",
        "header_success": "Success",
        "header_length": "Length",
        "header_saved_path": "Saved path",
        "header_save_error": "Save error",
        "header_error": "Error",
        "header_url": "URL",
        "header_accessible": "Accessible",
        "header_method": "Method",
        "header_path": "Path",
        "header_source": "Source",
        "header_sensitive_type": "Type",
        "header_masked_value": "Value",
        "header_confidence": "Confidence",
        "header_severity": "Severity",
        "header_location": "Location",
        "quick_success_only": "Success only",
        "quick_accessible_only": "Accessible only",
        "quick_high_only": "High only",
        "status_200_only": "Status 200 only",
        "filter": "Filter",
        "filter_type": "Type",
        "all": "All",
        "sensitive_type_all": "All",
        "sensitive_type_email": "Email",
        "sensitive_type_phone": "Phone",
        "sensitive_type_name": "Name",
        "sensitive_type_account": "Account",
        "sensitive_type_credential": "Credential",
        "sensitive_type_token": "Token",
        "sensitive_type_user_id": "User ID",
        "sensitive_type_other": "Other",
        "search_placeholder": "Enter search text",
        "reset": "Reset",
        "count_label": "Shown {visible} / Total {total}",
        "save_dialog_title": "Choose export base name",
        "save_dialog_filter": "Export base name (*.xlsx *.html);;All files (*)",
        "save_log_title": "Save log file",
        "save_log_filter": "Log files (*.log *.txt);;All files (*)",
        "scan_in_progress_title": "Already Running",
        "scan_in_progress_body": "A scan is already in progress.",
        "input_error_title": "Input Error",
        "security_warning_title": "Security Warning",
        "security_warning_body": "SSL certificate verification is disabled.\nUse this only for trusted targets.",
        "log_ssl_warning": "[Warning] SSL certificate verification is disabled.",
        "no_scan_title": "Stop",
        "no_scan_body": "There is no active scan to stop.",
        "log_cancel_requested": "[Stop requested] The scan will stop after the current request finishes.",
        "log_save_completed": "Saved: {path} (Excel + HTML)",
        "scan_complete_message": "Scanned {count} URL(s) (success {success}, failed {failed})",
        "log_error": "[Error] {message}",
        "execution_error_title": "Execution Error",
        "log_save_error": "[Save error] {message}",
        "output_save_failed": "save failed",
        "save_failed_state": "The scan completed, but saving the results failed: {message}",
        "save_failed_hint": "Scanned {count} URL(s) (success {success}, failed {failed}) / save failed",
        "save_error_title": "Save Error",
        "save_error_body": "The scan completed, but saving the results failed.\n{message}",
        "log_cancelled": "[Stopped] {message}",
        "running_hint": "The scan is running. You can follow progress in the log panel on the lower right.",
        "cancelling_hint": "The scan will stop after the current request finishes. Please wait a moment.",
        "result_selector_item": "{index}. [{status}] {url}",
        "yes": "Yes",
        "no": "No",
        "skipped": "Skipped",
        "save_results": "Save Results",
        "no_results_title": "Nothing to Save",
        "no_results_body": "There are no results to save yet. Run a scan first.",
        "output_not_saved": "Not saved",
        "state_saving": "Saving",
        "secondary_saving": "Saving",
        "save_in_progress_title": "Saving",
        "save_in_progress_body": "Results are currently being saved. Try again after it finishes.",
        "saving_hint": "The results are being saved. Please wait a moment.",
        "run_tooltip": "Start scanning the entered URL list.",
        "stop_tooltip": "Request cancellation for the active scan.",
        "save_results_tooltip": "Save the current results as Excel and HTML files.",
        "filter_tooltip": "Narrow the rows shown in this table.",
        "table_tooltip": "Double-click a cell to copy and inspect its full value.",
    },
}

SCAN_STATUS_LABELS = {
    "success": {"ko": "성공", "en": "Success"},
    "error": {"ko": "실패", "en": "Failed"},
    "unknown": {"ko": "알 수 없음", "en": "Unknown"},
}

JS_HEADER_KEYS = (
    "header_depth",
    "header_status",
    "header_success",
    "header_length",
    "header_saved_path",
    "header_save_error",
    "header_error",
    "header_url",
)
RESULT_HEADER_KEYS = ("header_status", "header_accessible", "header_method", "header_path", "header_source", "header_url")
PAGE_HEADER_KEYS = (
    "header_status",
    "header_length",
    "header_accessible",
    "header_method",
    "header_path",
    "header_source",
    "header_url",
)
SENSITIVE_HEADER_KEYS = (
    "header_sensitive_type",
    "header_masked_value",
    "header_confidence",
    "header_severity",
    "header_source",
    "header_location",
)
SENSITIVE_TYPE_FILTER_KEYS = (
    ("all", "sensitive_type_all"),
    ("email", "sensitive_type_email"),
    ("phone", "sensitive_type_phone"),
    ("name", "sensitive_type_name"),
    ("account", "sensitive_type_account"),
    ("credential", "sensitive_type_credential"),
    ("token", "sensitive_type_token"),
    ("user_id", "sensitive_type_user_id"),
    ("other", "sensitive_type_other"),
)


def _normalize_ui_language(value: object) -> str:
    return "en" if str(value or "").strip().lower() == "en" else "ko"


def _ui_text(language: str, key: str, **kwargs) -> str:
    normalized = _normalize_ui_language(language)
    template = UI_TEXTS[normalized].get(key) or UI_TEXTS["ko"].get(key) or key
    return template.format(**kwargs) if kwargs else template


def _scan_status_text(status: object, language: str) -> str:
    normalized = str(status or "").strip().lower()
    labels = SCAN_STATUS_LABELS.get(normalized)
    if labels is None:
        return str(status or "-")
    return labels[_normalize_ui_language(language)]


class NoScrollSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class SortableTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other) -> bool:
        left = self.data(Qt.ItemDataRole.UserRole)
        right = other.data(Qt.ItemDataRole.UserRole)
        if left is not None and right is not None:
            return left < right
        return super().__lt__(other)


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _table_sort_value(value: object) -> Optional[float]:
    text = str(value or "").strip()
    if not text or text == "-":
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def _normalize_sensitive_type(value: object) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if not normalized:
        return "other"
    mapping = {
        "email": "email",
        "e_mail": "email",
        "phone": "phone",
        "tel": "phone",
        "mobile": "phone",
        "person_name": "name",
        "fullname": "name",
        "full_name": "name",
        "displayname": "name",
        "display_name": "name",
        "name": "name",
        "account": "account",
        "account_id": "account",
        "account_like_id": "account",
        "credential": "credential",
        "credentials": "credential",
        "credential_like_string": "credential",
        "password": "credential",
        "passwd": "credential",
        "pwd": "credential",
        "secret": "credential",
        "token": "token",
        "access_token": "token",
        "refreshtoken": "token",
        "refresh_token": "token",
        "api_key": "token",
        "apikey": "token",
        "bearer": "token",
        "jwt": "token",
        "user_id": "user_id",
        "userid": "user_id",
        "username": "user_id",
        "loginid": "user_id",
        "login_id": "user_id",
    }
    return mapping.get(normalized, "other")


def _normalize_sensitive_severity(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"critical", "high", "medium", "low"}:
        return normalized
    if normalized in {"severe", "sev_high"}:
        return "high"
    if normalized in {"mid", "med"}:
        return "medium"
    if normalized:
        return normalized
    return "low"


def _status_text(status_code: object) -> str:
    if status_code is None:
        return "-"
    return str(status_code)


def _accessible_text(value: object, language: str = "ko") -> str:
    if value is True:
        return _ui_text(language, "yes")
    if value is False:
        return _ui_text(language, "no")
    return _ui_text(language, "skipped")


@dataclass
class ScanRequest:
    urls: List[str]
    config: Config


@dataclass
class TableTabBundle:
    widget: QWidget
    filter_label: QLabel
    filter_col: QComboBox
    filter_text: QLineEdit
    quick_check: QCheckBox
    clear_button: QPushButton
    count_label: QLabel
    table: QTableWidget
    header_keys: Tuple[str, ...]
    quick_filter_key: str


class ScanWorker(QObject):
    progress = Signal(str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal(str)

    def __init__(self, request: ScanRequest) -> None:
        super().__init__()
        self.request = request
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            execution = build_execution_context(self.request.config)
            execution.cancel_event = self.cancel_event
            result = discover_many(self.request.config, self.request.urls, progress=self._emit_progress, execution=execution)
            if self.cancel_event.is_set():
                raise ScanCancelled(CANCEL_MESSAGE)
        except ScanCancelled as exc:
            self.cancelled.emit(str(exc))
            return
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.finished.emit(result)

    def _emit_progress(self, message: str) -> None:
        self.progress.emit(message)

    def cancel(self) -> None:
        self.cancel_event.set()

    def is_cancel_requested(self) -> bool:
        return self.cancel_event.is_set()


class SaveWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, output_path: Path, batch_result: dict) -> None:
        super().__init__()
        self.output_path = output_path
        self.batch_result = batch_result

    def run(self) -> None:
        try:
            saved_paths = save_export_bundle(self.output_path, self.batch_result)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(saved_paths)


class CellDetailDialog(QDialog):
    def __init__(self, text: str, language: str = "ko", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.language = _normalize_ui_language(language)
        self.setWindowTitle(_ui_text(self.language, "cell_detail_title"))
        self.resize(720, 360)

        layout = QVBoxLayout(self)
        self.editor = QPlainTextEdit(self)
        self.editor.setReadOnly(False)
        self.editor.setPlainText(text)
        layout.addWidget(self.editor)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.copy_button = QPushButton(_ui_text(self.language, "copy"), self)
        self.close_button = QPushButton(_ui_text(self.language, "close"), self)
        self.copy_button.clicked.connect(self.copy_text)
        self.close_button.clicked.connect(self.accept)
        button_row.addWidget(self.copy_button)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

    def copy_text(self) -> None:
        QGuiApplication.clipboard().setText(self.editor.toPlainText())


class DiscoveryWindow(QMainWindow):
    def __init__(
        self,
        initial_url: Optional[str] = None,
        initial_output: Optional[str] = None,
        initial_js_output_dir: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.resize(1520, 920)
        self.settings = QSettings("RouteApiDiscovery", "RouteApiDiscovery")
        self.theme_mode = self._load_theme_mode()
        self.ui_language = self._load_ui_language()

        self.batch_result: Optional[dict] = None
        self.current_output_path: str = ""
        self.default_output_path = (initial_output or "discovery-result").strip() or "discovery-result"
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[ScanWorker] = None
        self.save_thread: Optional[QThread] = None
        self.save_worker: Optional[SaveWorker] = None
        self.state_mode = "idle"
        self.last_error_message = ""
        self.last_save_error_message = ""
        self.last_save_failed = False
        self.current_target_value = "-"
        self.current_output_value = "-"
        self.current_output_save_failed = False

        self.js_rows: List[Tuple[str, str, str, str, str, str, str, str]] = []
        self.page_rows: List[Tuple[str, str, str, str, str, str, str]] = []
        self.api_rows: List[Tuple[str, str, str, str, str, str]] = []
        self.sensitive_records: List[dict] = []

        self._build_ui(
            initial_url=initial_url,
            initial_output=initial_output,
            initial_js_output_dir=initial_js_output_dir,
        )
        self._sync_theme_toggle()
        self._refresh_language_texts()
        self._apply_styles()
        self._set_idle_state()

    def closeEvent(self, event) -> None:
        if self.worker_thread is not None and self.worker_thread.isRunning():
            if self.worker is not None and not self.worker.is_cancel_requested():
                self.cancel_scan()
                QMessageBox.information(
                    self,
                    self.tr("close_scan_request_title"),
                    self.tr("close_scan_request_body"),
                )
            else:
                QMessageBox.information(
                    self,
                    self.tr("close_scan_wait_title"),
                    self.tr("close_scan_wait_body"),
                )
            event.ignore()
            return
        if self.save_thread is not None and self.save_thread.isRunning():
            QMessageBox.information(
                self,
                self.tr("save_in_progress_title"),
                self.tr("save_in_progress_body"),
            )
            event.ignore()
            return
        super().closeEvent(event)

    def _build_ui(
        self,
        initial_url: Optional[str],
        initial_output: Optional[str],
        initial_js_output_dir: Optional[str],
    ) -> None:
        self.central = QWidget(self)
        self.setCentralWidget(self.central)

        root = QVBoxLayout(self.central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self.toolbar_card = self._build_workbench_bar()
        root.addWidget(self.toolbar_card)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.central)
        self.splitter.setChildrenCollapsible(False)
        root.addWidget(self.splitter, 1)

        self.left_panel = self._build_left_panel(
            initial_url=initial_url,
            initial_output=initial_output,
            initial_js_output_dir=initial_js_output_dir,
        )
        self.right_panel = self._build_right_panel()
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([400, 1120])

    def _build_workbench_bar(self) -> QWidget:
        card = QFrame(self.central)
        card.setObjectName("toolbarCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.setSpacing(1)
        self.app_title_label = QLabel(card)
        self.app_title_label.setObjectName("workbenchTitle")
        self.app_subtitle_label = QLabel(card)
        self.app_subtitle_label.setObjectName("workbenchSubtitle")
        title_block.addWidget(self.app_title_label)
        title_block.addWidget(self.app_subtitle_label)
        layout.addLayout(title_block)

        layout.addSpacing(10)

        self.run_button = QPushButton(card)
        self.run_button.setObjectName("primaryRunButton")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = QPushButton(card)
        self.stop_button.setObjectName("toolbarButton")
        self.stop_button.clicked.connect(self.cancel_scan)
        self.stop_button.setEnabled(False)
        self.save_again_button = QPushButton(card)
        self.save_again_button.setObjectName("toolbarButton")
        self.save_again_button.clicked.connect(self.save_results)
        self.save_again_button.setEnabled(False)
        layout.addWidget(self.run_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.save_again_button)

        layout.addSpacing(10)

        self.action_title_label = QLabel(card)
        self.action_title_label.setObjectName("toolbarStatusLabel")
        self.state_chip = QLabel(card)
        self.state_chip.setObjectName("stateChip")
        self.secondary_chip = QLabel(card)
        self.secondary_chip.setObjectName("mutedChip")
        layout.addWidget(self.action_title_label)
        layout.addWidget(self.state_chip)
        layout.addWidget(self.secondary_chip)

        layout.addStretch(1)

        self.language_label = QLabel(card)
        self.language_label.setObjectName("toolbarMetaLabel")
        self.language_combo = QComboBox(card)
        self.language_combo.addItem("", "ko")
        self.language_combo.addItem("", "en")
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.language_combo.setMinimumWidth(110)
        self.dark_mode_check = QCheckBox(card)
        self.dark_mode_check.setObjectName("darkModeToggle")
        self.dark_mode_check.toggled.connect(self._on_dark_mode_toggled)
        self.settings_button = QPushButton(card)
        self.settings_button.setObjectName("toolbarButton")
        self.settings_button.clicked.connect(self._focus_options_panel)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combo)
        layout.addWidget(self.dark_mode_check)
        layout.addWidget(self.settings_button)

        return card

    def _build_left_panel(
        self,
        initial_url: Optional[str],
        initial_output: Optional[str],
        initial_js_output_dir: Optional[str],
    ) -> QWidget:
        container = QWidget(self.splitter)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.left_scroll = QScrollArea(container)
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.left_scroll)

        self.left_content = QWidget(self.left_scroll)
        self.left_scroll.setWidget(self.left_content)
        self.left_layout = QVBoxLayout(self.left_content)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(14)

        self._init_left_cards(
            initial_url=initial_url,
            initial_output=initial_output,
            initial_js_output_dir=initial_js_output_dir,
        )
        self.left_layout.addStretch(1)
        container.setMinimumWidth(340)
        container.setMaximumWidth(430)
        return container

    def _build_right_panel(self) -> QWidget:
        container = QWidget(self.splitter)
        self.right_panel = container
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self._init_right_header(layout)
        self._init_right_body(layout)
        return container

    def tr(self, key: str, **kwargs) -> str:
        return _ui_text(self.ui_language, key, **kwargs)

    def _load_ui_language(self) -> str:
        saved = str(self.settings.value("ui_language", "ko") or "ko").strip().lower()
        return saved if saved in {"ko", "en"} else "ko"

    def _sync_language_selector(self) -> None:
        if not hasattr(self, "language_combo"):
            return
        self.language_combo.blockSignals(True)
        self.language_combo.setItemText(0, self.tr("language_ko"))
        self.language_combo.setItemText(1, self.tr("language_en"))
        self.language_combo.setCurrentIndex(0 if self.ui_language == "ko" else 1)
        self.language_combo.blockSignals(False)

    def _localized_headers(self, header_keys: Tuple[str, ...]) -> List[str]:
        return [self.tr(key) for key in header_keys]

    def _set_current_target(self, value: str) -> None:
        self.current_target_value = value
        self.current_target_label.setText(self.tr("current_target", value=value))

    def _set_current_output(self, value: str, save_failed: bool = False) -> None:
        self.current_output_value = value
        self.current_output_save_failed = save_failed
        if save_failed:
            display_value = self.tr("output_save_failed")
        elif value:
            display_value = value
        elif self.batch_result:
            display_value = self.tr("output_not_saved")
        else:
            display_value = "-"
        self.current_output_label.setText(self.tr("current_output", value=display_value))

    def _localize_table_bundle(self, bundle: TableTabBundle) -> None:
        headers = self._localized_headers(bundle.header_keys)
        current_index = bundle.filter_col.currentIndex()
        bundle.filter_label.setText(self.tr("filter"))
        bundle.filter_label.setToolTip(self.tr("filter_tooltip"))
        bundle.filter_col.blockSignals(True)
        bundle.filter_col.clear()
        bundle.filter_col.addItem(self.tr("all"))
        for header in headers:
            bundle.filter_col.addItem(header)
        bundle.filter_col.setCurrentIndex(max(0, min(current_index, bundle.filter_col.count() - 1)))
        bundle.filter_col.blockSignals(False)
        bundle.filter_text.setPlaceholderText(self.tr("search_placeholder"))
        bundle.filter_col.setToolTip(self.tr("filter_tooltip"))
        bundle.filter_text.setToolTip(self.tr("filter_tooltip"))
        bundle.quick_check.setText(self.tr(bundle.quick_filter_key))
        bundle.quick_check.setToolTip(self.tr("filter_tooltip"))
        bundle.clear_button.setText(self.tr("reset"))
        bundle.clear_button.setToolTip(self.tr("filter_tooltip"))
        bundle.count_label.setText(self.tr("count_label", visible=0, total=0))
        bundle.table.setHorizontalHeaderLabels(headers)
        bundle.table.setToolTip(self.tr("table_tooltip"))

    def _localize_sensitive_type_filter(self) -> None:
        if not hasattr(self, "sensitive_type_combo"):
            return
        current_value = self.sensitive_type_combo.currentData()
        self.sensitive_type_label.setText(self.tr("filter_type"))
        self.sensitive_type_combo.blockSignals(True)
        self.sensitive_type_combo.clear()
        for value, key in SENSITIVE_TYPE_FILTER_KEYS:
            self.sensitive_type_combo.addItem(self.tr(key), value)
        target_index = self.sensitive_type_combo.findData(current_value)
        self.sensitive_type_combo.setCurrentIndex(0 if target_index < 0 else target_index)
        self.sensitive_type_combo.blockSignals(False)

    def _refresh_language_texts(self) -> None:
        self.setWindowTitle(self.tr("window_title"))
        self._sync_language_selector()

        self.app_title_label.setText(self.tr("app_title"))
        self.app_subtitle_label.setText(self.tr("app_subtitle"))
        self.url_title_label.setText(self.tr("target_url"))
        self.run_button.setText(self.tr("run"))
        self.run_button.setToolTip(self.tr("run_tooltip"))
        self.stop_button.setText(self.tr("stop"))
        self.stop_button.setToolTip(self.tr("stop_tooltip"))
        self.url_input.setPlaceholderText(self.tr("url_placeholder"))

        self.output_title_label.setText(self.tr("output_file"))
        self.output_input.setPlaceholderText(self.tr("output_placeholder"))
        self.output_browse_button.setText(self.tr("browse"))
        self.output_hint_label.setText(self.tr("output_hint"))
        self.save_again_button.setText(self.tr("save_results"))
        self.save_again_button.setToolTip(self.tr("save_results_tooltip"))

        self.header_title_label.setText(self.tr("request_headers"))
        self.header_input.setPlaceholderText(self.tr("headers_placeholder"))
        self.option_title_label.setText(self.tr("options"))
        self.max_js_label.setText(self.tr("max_js"))
        self.max_depth_label.setText(self.tr("max_depth"))
        self.timeout_label.setText(self.tr("timeout"))
        self.recursive_depth_label.setText(self.tr("recursive_depth"))
        self.max_workers_label.setText(self.tr("max_workers"))
        self.request_delay_label.setText(self.tr("request_delay"))
        self.proxy_label.setText(self.tr("proxy"))
        self.language_label.setText(self.tr("language"))
        self.timeout_spin.setSuffix(self.tr("timeout_suffix"))
        self.request_delay_spin.setSuffix(self.tr("timeout_suffix"))
        self.proxy_input.setPlaceholderText(self.tr("proxy_placeholder"))
        self.js_output_dir_label.setText(self.tr("js_output_dir"))
        self.js_output_dir_input.setPlaceholderText(self.tr("js_output_dir_placeholder"))
        self.js_output_dir_button.setText(self.tr("browse"))
        self.recursive_scan_check.setText(self.tr("recursive_scan"))
        self.include_subdomains_check.setText(self.tr("include_subdomains"))
        self.excluded_subdomains_label.setText(self.tr("excluded_subdomains"))
        self.excluded_subdomains_input.setPlaceholderText(self.tr("excluded_subdomains_placeholder"))
        self.skip_probe_check.setText(self.tr("skip_probe"))
        self.verify_ssl_check.setText(self.tr("verify_ssl"))

        self.action_title_label.setText(self.tr("execution_status"))
        self.settings_button.setText(self.tr("settings"))
        self.left_status_title_label.setText(self.tr("execution_status"))

        self.results_title_label.setText(self.tr("results"))
        self.result_selector_label.setText(self.tr("result_selector"))
        self.dark_mode_check.setText(self.tr("dark_mode"))
        self.card_js_title.setText(self.tr("metric_js"))
        self.card_page_title.setText(self.tr("metric_page"))
        self.card_api_title.setText(self.tr("metric_api"))
        self.card_recursive_title.setText(self.tr("metric_recursive"))
        self.card_sensitive_total_title.setText(self.tr("metric_sensitive_total"))
        self.card_sensitive_high_title.setText(self.tr("metric_sensitive_high"))
        self.empty_state_label.setText(self.tr("empty_state"))
        self.running_state_label.setText(self.tr("running_state"))

        self.tab_widget.setTabText(0, self.tr("tab_summary"))
        self.tab_widget.setTabText(1, self.tr("tab_sensitive"))
        self.tab_widget.setTabText(2, self.tr("tab_js"))
        self.tab_widget.setTabText(3, self.tr("tab_page"))
        self.tab_widget.setTabText(4, self.tr("tab_api"))
        self.log_title_label.setText(self.tr("tab_log"))
        self.log_clear_button.setText(self.tr("clear_log"))
        self.log_save_button.setText(self.tr("save_log"))

        self._localize_table_bundle(self.sensitive_bundle)
        self._localize_sensitive_type_filter()
        self._localize_table_bundle(self.js_bundle)
        self._localize_table_bundle(self.page_bundle)
        self._localize_table_bundle(self.api_bundle)
        self.page_status_200_check.setText(self.tr("status_200_only"))
        self.api_status_200_check.setText(self.tr("status_200_only"))

        self._set_current_target(self.current_target_value)
        self._set_current_output(self.current_output_value, save_failed=self.current_output_save_failed)

    def _on_language_changed(self, index: int) -> None:
        language = self.language_combo.itemData(index)
        if language is None:
            return
        normalized = _normalize_ui_language(language)
        if normalized == self.ui_language:
            return

        selected_index = self.result_selector.currentIndex()
        self.ui_language = normalized
        self.settings.setValue("ui_language", self.ui_language)
        self._refresh_language_texts()

        if self.state_mode == "running":
            self._set_running_state()
        elif self.state_mode == "cancelling":
            self._set_cancelling_state()
        elif self.state_mode == "saving":
            self._set_saving_state()
        elif self.state_mode == "ready" and self.batch_result:
            result_count = len(self.batch_result.get("results", []))
            success_count = _safe_int(self.batch_result.get("success_count", 0), 0)
            self._set_result_ready_state(
                self.tr(
                    "scan_complete_message",
                    count=result_count,
                    success=success_count,
                    failed=result_count - success_count,
                )
            )
        elif self.state_mode == "error":
            if self.last_save_failed and self.batch_result:
                result_count = len(self.batch_result.get("results", []))
                success_count = _safe_int(self.batch_result.get("success_count", 0), 0)
                save_error = self.last_save_error_message or self.last_error_message
                self._set_error_state(self.tr("save_failed_state", message=save_error))
                self.last_save_error_message = save_error
                self.last_save_failed = True
                self.left_state_hint.setText(
                    self.tr(
                        "save_failed_hint",
                        count=result_count,
                        success=success_count,
                        failed=result_count - success_count,
                    )
                )
            else:
                self._set_error_state(self.last_error_message)
        else:
            self._set_idle_state()

        if self.batch_result and self.batch_result.get("results"):
            self._refresh_result_selector(selected_index=selected_index)

    def _set_scan_inputs_enabled(self, enabled: bool) -> None:
        controls = (
            self.url_input,
            self.output_input,
            self.output_browse_button,
            self.header_input,
            self.max_js_spin,
            self.max_depth_spin,
            self.timeout_spin,
            self.recursive_scan_check,
            self.include_subdomains_check,
            self.excluded_subdomains_input,
            self.skip_probe_check,
            self.verify_ssl_check,
            self.max_workers_spin,
            self.request_delay_spin,
            self.proxy_input,
            self.js_output_dir_input,
            self.js_output_dir_button,
        )
        for control in controls:
            control.setEnabled(enabled)
        self.recursive_depth_spin.setEnabled(enabled and self.recursive_scan_check.isChecked())

    def _init_left_cards(
        self,
        initial_url: Optional[str],
        initial_output: Optional[str],
        initial_js_output_dir: Optional[str],
    ) -> None:
        url_card, url_layout = self._create_card("targetCard")
        self.url_title_label = QLabel(url_card)
        self.url_title_label.setObjectName("sectionTitle")
        url_layout.addWidget(self.url_title_label)

        self.url_input = QPlainTextEdit(url_card)
        self.url_input.setMinimumHeight(118)
        self.url_input.setMaximumHeight(180)
        self.url_input.setPlainText((initial_url or "").strip())
        url_layout.addWidget(self.url_input)
        self.left_layout.addWidget(url_card)

        output_card, output_layout = self._create_card("outputCard")
        self.output_title_label = QLabel(output_card)
        self.output_title_label.setObjectName("sectionTitle")
        output_layout.addWidget(self.output_title_label)
        output_row = QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.setSpacing(8)
        self.output_input = QLineEdit(output_card)
        self.output_input.setText((initial_output or self.default_output_path).strip())
        self.output_browse_button = QPushButton(output_card)
        self.output_browse_button.clicked.connect(self.choose_output_file)
        output_row.addWidget(self.output_input, 1)
        output_row.addWidget(self.output_browse_button)
        output_layout.addLayout(output_row)
        self.output_hint_label = QLabel(output_card)
        self.output_hint_label.setObjectName("hintLabel")
        self.output_hint_label.setWordWrap(True)
        output_layout.addWidget(self.output_hint_label)
        self.left_layout.addWidget(output_card)

        header_card, header_layout = self._create_card("headerCard")
        self.header_title_label = QLabel(header_card)
        self.header_title_label.setObjectName("sectionTitle")
        header_layout.addWidget(self.header_title_label)
        self.header_input = QPlainTextEdit(header_card)
        self.header_input.setMinimumHeight(100)
        self.header_input.setMaximumHeight(140)
        header_layout.addWidget(self.header_input)
        self.left_layout.addWidget(header_card)

        option_card, option_layout = self._create_card("optionCard")
        self.option_card = option_card
        self.option_title_label = QLabel(option_card)
        self.option_title_label.setObjectName("sectionTitle")
        option_layout.addWidget(self.option_title_label)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.max_js_spin = NoScrollSpinBox(option_card)
        self.max_js_spin.setRange(1, 5000)
        self.max_js_spin.setValue(50)
        self.max_depth_spin = NoScrollSpinBox(option_card)
        self.max_depth_spin.setRange(0, 10)
        self.max_depth_spin.setValue(2)
        self.timeout_spin = NoScrollDoubleSpinBox(option_card)
        self.timeout_spin.setRange(1.0, 120.0)
        self.timeout_spin.setSingleStep(1.0)
        self.timeout_spin.setValue(15.0)
        self.recursive_scan_check = QCheckBox(option_card)
        self.include_subdomains_check = QCheckBox(option_card)
        self.include_subdomains_check.setChecked(True)
        self.excluded_subdomains_label = QLabel(option_card)
        self.excluded_subdomains_input = QLineEdit(option_card)
        self.recursive_depth_spin = NoScrollSpinBox(option_card)
        self.recursive_depth_spin.setRange(0, 10)
        self.recursive_depth_spin.setValue(1)
        self.max_workers_spin = NoScrollSpinBox(option_card)
        self.max_workers_spin.setRange(1, 32)
        self.max_workers_spin.setValue(1)
        self.request_delay_spin = NoScrollDoubleSpinBox(option_card)
        self.request_delay_spin.setRange(0.0, 60.0)
        self.request_delay_spin.setSingleStep(0.1)
        self.request_delay_spin.setValue(0.0)
        self.proxy_label = QLabel(option_card)
        self.proxy_input = QLineEdit(option_card)
        self.js_output_dir_label = QLabel(option_card)
        self.js_output_dir_input = QLineEdit(option_card)
        self.js_output_dir_input.setText(initial_js_output_dir or "")
        self.js_output_dir_button = QPushButton(option_card)
        self.js_output_dir_button.clicked.connect(self.choose_js_output_dir)
        self.skip_probe_check = QCheckBox(option_card)
        self.verify_ssl_check = QCheckBox(option_card)
        self.verify_ssl_check.setChecked(True)

        self.max_js_label = QLabel(option_card)
        self.max_depth_label = QLabel(option_card)
        self.timeout_label = QLabel(option_card)
        self.recursive_depth_label = QLabel(option_card)
        self.max_workers_label = QLabel(option_card)
        self.request_delay_label = QLabel(option_card)

        grid.addWidget(self.max_js_label, 0, 0)
        grid.addWidget(self.max_js_spin, 0, 1)
        grid.addWidget(self.max_depth_label, 1, 0)
        grid.addWidget(self.max_depth_spin, 1, 1)
        grid.addWidget(self.timeout_label, 2, 0)
        grid.addWidget(self.timeout_spin, 2, 1)
        advanced_label = QLabel("Advanced options", option_card)
        advanced_label.setObjectName("subsectionTitle")
        grid.addWidget(advanced_label, 3, 0, 1, 2)
        grid.addWidget(self.recursive_scan_check, 4, 0, 1, 2)
        grid.addWidget(self.include_subdomains_check, 5, 0, 1, 2)
        grid.addWidget(self.excluded_subdomains_label, 6, 0)
        grid.addWidget(self.excluded_subdomains_input, 6, 1)
        grid.addWidget(self.recursive_depth_label, 7, 0)
        grid.addWidget(self.recursive_depth_spin, 7, 1)
        grid.addWidget(self.skip_probe_check, 8, 0, 1, 2)
        grid.addWidget(self.verify_ssl_check, 9, 0, 1, 2)
        grid.addWidget(self.max_workers_label, 10, 0)
        grid.addWidget(self.max_workers_spin, 10, 1)
        grid.addWidget(self.request_delay_label, 11, 0)
        grid.addWidget(self.request_delay_spin, 11, 1)
        grid.addWidget(self.proxy_label, 12, 0)
        grid.addWidget(self.proxy_input, 12, 1)
        grid.addWidget(self.js_output_dir_label, 13, 0)
        js_output_row = QHBoxLayout()
        js_output_row.setContentsMargins(0, 0, 0, 0)
        js_output_row.addWidget(self.js_output_dir_input, 1)
        js_output_row.addWidget(self.js_output_dir_button)
        grid.addLayout(js_output_row, 13, 1)
        option_layout.addLayout(grid)
        self.left_layout.addWidget(option_card)

        action_card, action_layout = self._create_card("actionCard")
        self.left_status_title_label = QLabel(action_card)
        self.left_status_title_label.setObjectName("sectionTitle")
        action_layout.addWidget(self.left_status_title_label)
        self.left_state_hint = QLabel(action_card)
        self.left_state_hint.setObjectName("hintLabel")
        self.left_state_hint.setWordWrap(True)
        action_layout.addWidget(self.left_state_hint)
        self.left_layout.addWidget(action_card)

        self.recursive_scan_check.toggled.connect(self.recursive_depth_spin.setEnabled)
        self.recursive_depth_spin.setEnabled(self.recursive_scan_check.isChecked())

    def _init_right_header(self, parent_layout: QVBoxLayout) -> None:
        header_card, header_layout = self._create_card("resultsHeaderCard")
        header_layout.setSpacing(10)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        self.results_title_label = QLabel(header_card)
        self.results_title_label.setObjectName("resultsTitle")

        self.result_selector_label = QLabel(header_card)
        self.result_selector = QComboBox(header_card)
        self.result_selector.currentIndexChanged.connect(self._on_result_changed)
        self.result_selector.setMinimumWidth(320)

        top_row.addWidget(self.results_title_label)
        top_row.addStretch(1)
        top_row.addWidget(self.result_selector_label)
        top_row.addWidget(self.result_selector)
        header_layout.addLayout(top_row)

        context_row = QHBoxLayout()
        context_row.setContentsMargins(0, 0, 0, 0)
        context_row.setSpacing(10)
        self.current_target_label = QLabel(header_card)
        self.current_output_label = QLabel(header_card)
        self.current_target_label.setObjectName("contextLabel")
        self.current_output_label.setObjectName("contextLabel")
        self.current_target_label.setWordWrap(True)
        self.current_output_label.setWordWrap(True)
        context_row.addWidget(self.current_target_label, 1)
        context_row.addWidget(self.current_output_label, 1)
        header_layout.addLayout(context_row)

        cards = QHBoxLayout()
        cards.setContentsMargins(0, 2, 0, 0)
        cards.setSpacing(8)
        self.card_js_frame, self.card_js_title, self.card_js_value = self._create_metric_card(header_card)
        self.card_page_frame, self.card_page_title, self.card_page_value = self._create_metric_card(header_card)
        self.card_api_frame, self.card_api_title, self.card_api_value = self._create_metric_card(header_card)
        self.card_recursive_frame, self.card_recursive_title, self.card_recursive_value = self._create_metric_card(header_card)
        self.card_sensitive_total_frame, self.card_sensitive_total_title, self.card_sensitive_total_value = (
            self._create_metric_card(header_card)
        )
        self.card_sensitive_high_frame, self.card_sensitive_high_title, self.card_sensitive_high_value = (
            self._create_metric_card(header_card)
        )
        cards.addWidget(self.card_js_frame, 1)
        cards.addWidget(self.card_page_frame, 1)
        cards.addWidget(self.card_api_frame, 1)
        cards.addWidget(self.card_recursive_frame, 1)
        cards.addWidget(self.card_sensitive_total_frame, 1)
        cards.addWidget(self.card_sensitive_high_frame, 1)
        header_layout.addLayout(cards)
        parent_layout.addWidget(header_card)

    def _init_right_body(self, parent_layout: QVBoxLayout) -> None:
        self.result_stack = QStackedWidget(self.right_panel)
        parent_layout.addWidget(self.result_stack, 1)

        empty_page = QWidget(self.result_stack)
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setContentsMargins(16, 16, 16, 16)
        empty_layout.addStretch(1)
        self.empty_state_label = QLabel(empty_page)
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_label.setObjectName("emptyStateLabel")
        empty_layout.addWidget(self.empty_state_label)
        empty_layout.addStretch(1)
        self.result_stack.addWidget(empty_page)

        running_page = QWidget(self.result_stack)
        running_layout = QVBoxLayout(running_page)
        running_layout.setContentsMargins(16, 16, 16, 16)
        running_layout.addStretch(1)
        self.running_state_label = QLabel(running_page)
        self.running_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.running_state_label.setObjectName("runningStateLabel")
        running_layout.addWidget(self.running_state_label)
        running_layout.addStretch(1)
        self.result_stack.addWidget(running_page)

        content_page = QWidget(self.result_stack)
        content_layout = QVBoxLayout(content_page)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.tab_widget = QTabWidget(content_page)
        self.tab_widget.setObjectName("resultTabs")
        self.tab_widget.setDocumentMode(True)
        content_layout.addWidget(self.tab_widget, 1)

        self.summary_text = QTextEdit(content_page)
        self.summary_text.setReadOnly(True)
        self.summary_text.setObjectName("summaryViewer")
        self.tab_widget.addTab(self.summary_text, "")

        self.sensitive_bundle = self._create_table_tab(
            header_keys=SENSITIVE_HEADER_KEYS,
            quick_filter_key="quick_high_only",
            quick_filter_attr="sensitive_high_only_check",
            on_apply=self._apply_sensitive_filters,
            parent=content_page,
        )
        self.sensitive_tab = self.sensitive_bundle.widget
        self.sensitive_filter_col = self.sensitive_bundle.filter_col
        self.sensitive_filter_text = self.sensitive_bundle.filter_text
        self.sensitive_count_label = self.sensitive_bundle.count_label
        self.sensitive_table = self.sensitive_bundle.table
        self.sensitive_table.setColumnWidth(0, 120)
        self.sensitive_table.setColumnWidth(1, 240)
        self.sensitive_table.setColumnWidth(2, 90)
        self.sensitive_table.setColumnWidth(3, 90)
        self.sensitive_table.setColumnWidth(4, 320)
        self.sensitive_table.setColumnWidth(5, 220)
        sensitive_filter_bar = self.sensitive_tab.layout().itemAt(0).layout()
        self.sensitive_type_label = QLabel(self.sensitive_tab)
        self.sensitive_type_combo = QComboBox(self.sensitive_tab)
        self.sensitive_type_combo.currentIndexChanged.connect(lambda _: self._apply_sensitive_filters())
        sensitive_filter_bar.insertWidget(3, self.sensitive_type_label)
        sensitive_filter_bar.insertWidget(4, self.sensitive_type_combo)
        self.tab_widget.addTab(self.sensitive_tab, "")

        self.js_bundle = self._create_table_tab(
            header_keys=JS_HEADER_KEYS,
            quick_filter_key="quick_success_only",
            quick_filter_attr="js_success_only_check",
            on_apply=self._apply_js_filters,
            parent=content_page,
        )
        self.js_tab = self.js_bundle.widget
        self.js_filter_col = self.js_bundle.filter_col
        self.js_filter_text = self.js_bundle.filter_text
        self.js_count_label = self.js_bundle.count_label
        self.js_table = self.js_bundle.table
        self.tab_widget.addTab(self.js_tab, "")

        self.page_bundle = self._create_table_tab(
            header_keys=PAGE_HEADER_KEYS,
            quick_filter_key="quick_accessible_only",
            quick_filter_attr="page_accessible_only_check",
            on_apply=self._apply_page_filters,
            parent=content_page,
        )
        self.page_tab = self.page_bundle.widget
        self.page_filter_col = self.page_bundle.filter_col
        self.page_filter_text = self.page_bundle.filter_text
        self.page_count_label = self.page_bundle.count_label
        self.page_table = self.page_bundle.table
        self.page_status_200_check = QCheckBox(self.page_tab)
        self.page_status_200_check.toggled.connect(lambda _: self._apply_page_filters())
        self.page_tab.layout().itemAt(0).layout().addWidget(self.page_status_200_check)
        self.tab_widget.addTab(self.page_tab, "")

        self.api_bundle = self._create_table_tab(
            header_keys=RESULT_HEADER_KEYS,
            quick_filter_key="quick_accessible_only",
            quick_filter_attr="api_accessible_only_check",
            on_apply=self._apply_api_filters,
            parent=content_page,
        )
        self.api_tab = self.api_bundle.widget
        self.api_filter_col = self.api_bundle.filter_col
        self.api_filter_text = self.api_bundle.filter_text
        self.api_count_label = self.api_bundle.count_label
        self.api_table = self.api_bundle.table
        self.api_status_200_check = QCheckBox(self.api_tab)
        self.api_status_200_check.toggled.connect(lambda _: self._apply_api_filters())
        self.api_tab.layout().itemAt(0).layout().addWidget(self.api_status_200_check)
        self.tab_widget.addTab(self.api_tab, "")

        log_card, log_layout = self._create_card("logCard")
        log_header = QHBoxLayout()
        log_header.setContentsMargins(0, 0, 0, 0)
        log_header.setSpacing(8)
        self.log_title_label = QLabel(log_card)
        self.log_title_label.setObjectName("sectionTitle")
        self.log_clear_button = QPushButton(log_card)
        self.log_clear_button.setObjectName("toolbarButton")
        self.log_save_button = QPushButton(log_card)
        self.log_save_button.setObjectName("toolbarButton")
        log_header.addWidget(self.log_title_label)
        log_header.addStretch(1)
        log_header.addWidget(self.log_clear_button)
        log_header.addWidget(self.log_save_button)
        log_layout.addLayout(log_header)

        self.log_text = QPlainTextEdit(log_card)
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("logViewer")
        log_font = QFont("Consolas")
        log_font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_text.setFont(log_font)
        self.log_text.setMinimumHeight(180)
        self.log_text.setMaximumHeight(240)
        log_layout.addWidget(self.log_text)
        self.log_clear_button.clicked.connect(lambda: self.log_text.clear())
        self.log_save_button.clicked.connect(self._save_log)
        content_layout.addWidget(log_card)

        self.result_stack.addWidget(content_page)

    def _create_card(self, object_name: str) -> Tuple[QFrame, QVBoxLayout]:
        card = QFrame(self.central)
        card.setObjectName(object_name)
        card.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        return card, layout

    def _create_metric_card(self, parent: QWidget) -> Tuple[QFrame, QLabel, QLabel]:
        frame = QFrame(parent)
        frame.setObjectName("metricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        title_label = QLabel(frame)
        title_label.setObjectName("metricTitle")
        value_label = QLabel("0", frame)
        value_label.setObjectName("metricValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return frame, title_label, value_label

    def _create_table_tab(
        self,
        header_keys: Tuple[str, ...],
        quick_filter_key: str,
        quick_filter_attr: str,
        on_apply,
        parent: QWidget,
    ) -> TableTabBundle:
        tab = QWidget(parent)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        filter_bar = QHBoxLayout()
        filter_bar.setContentsMargins(0, 0, 0, 0)
        filter_bar.setSpacing(8)
        filter_label = QLabel(tab)
        filter_bar.addWidget(filter_label)

        filter_col = QComboBox(tab)
        filter_col.currentIndexChanged.connect(lambda _: on_apply())
        filter_bar.addWidget(filter_col)

        filter_text = QLineEdit(tab)
        filter_text.textChanged.connect(lambda _: on_apply())
        filter_bar.addWidget(filter_text, 1)

        quick_check = QCheckBox(tab)
        setattr(self, quick_filter_attr, quick_check)
        quick_check.toggled.connect(lambda _: on_apply())
        filter_bar.addWidget(quick_check)

        clear_button = QPushButton(tab)
        clear_button.clicked.connect(lambda: self._clear_filter_widgets(filter_col, filter_text, quick_check, on_apply))
        filter_bar.addWidget(clear_button)
        layout.addLayout(filter_bar)

        count_row = QHBoxLayout()
        count_row.setContentsMargins(0, 0, 0, 0)
        count_row.addStretch(1)
        count_label = QLabel(tab)
        count_label.setObjectName("filterCountLabel")
        count_row.addWidget(count_label)
        layout.addLayout(count_row)

        table = QTableWidget(tab)
        table.setColumnCount(len(header_keys))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setWordWrap(False)
        table.setShowGrid(False)
        table.setSortingEnabled(True)
        table.cellDoubleClicked.connect(lambda row, col, current=table: self._on_table_double_click(current, row, col))
        layout.addWidget(table, 1)
        return TableTabBundle(
            widget=tab,
            filter_label=filter_label,
            filter_col=filter_col,
            filter_text=filter_text,
            quick_check=quick_check,
            clear_button=clear_button,
            count_label=count_label,
            table=table,
            header_keys=header_keys,
            quick_filter_key=quick_filter_key,
        )

    def _clear_filter_widgets(
        self,
        combo: QComboBox,
        text: QLineEdit,
        check: QCheckBox,
        on_apply,
    ) -> None:
        combo.setCurrentIndex(0)
        text.clear()
        check.setChecked(False)
        if check is getattr(self, "page_accessible_only_check", None):
            self.page_status_200_check.setChecked(False)
        elif check is getattr(self, "api_accessible_only_check", None):
            self.api_status_200_check.setChecked(False)
        elif check is getattr(self, "sensitive_high_only_check", None):
            if hasattr(self, "sensitive_type_combo"):
                self.sensitive_type_combo.setCurrentIndex(0)
        on_apply()

    def _apply_styles(self) -> None:
        palette = self._theme_palette()
        stylesheet = """
            QWidget {{
                background-color: {window_bg};
                color: {text_primary};
                font-family: "Segoe UI", "Noto Sans KR", sans-serif;
                font-size: 13px;
            }}
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QLabel {{
                background: transparent;
            }}
            QSplitter::handle {{
                background: {splitter_handle};
                margin: 6px 8px;
                border-radius: 4px;
            }}
            QLabel#workbenchTitle {{
                color: {text_primary};
                font-size: 19px;
                font-weight: 800;
            }}
            QLabel#workbenchSubtitle {{
                color: {text_muted};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#resultsTitle {{
                color: {text_primary};
                font-size: 16px;
                font-weight: 800;
            }}
            QLabel#sectionTitle {{
                color: {text_primary};
                font-size: 13px;
                font-weight: 800;
            }}
            QLabel#subsectionTitle {{
                color: {text_muted};
                font-size: 11px;
                font-weight: 800;
                padding-top: 6px;
                text-transform: uppercase;
            }}
            QLabel#hintLabel, QLabel#contextLabel {{
                color: {text_secondary};
                font-size: 12px;
                font-weight: 600;
                line-height: 1.35em;
            }}
            QLabel#toolbarStatusLabel, QLabel#toolbarMetaLabel {{
                color: {text_muted};
                font-size: 12px;
                font-weight: 700;
            }}
            QFrame#toolbarCard, QFrame#targetCard, QFrame#outputCard, QFrame#headerCard, QFrame#optionCard,
            QFrame#actionCard, QFrame#resultsHeaderCard, QFrame#logCard {{
                background: {surface_bg};
                border: 1px solid {surface_border};
                border-radius: 10px;
            }}
            QFrame#metricCard {{
                background: {metric_bg};
                border: 1px solid {surface_border};
                border-radius: 10px;
            }}
            QLabel#metricTitle {{
                color: {text_muted};
                font-size: 12px;
                font-weight: 600;
            }}
            QLabel#metricValue {{
                color: {text_primary};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#filterCountLabel {{
                color: {text_subtle};
                font-size: 12px;
                font-weight: 600;
            }}
            QLabel#stateChip, QLabel#mutedChip {{
                border-radius: 11px;
                padding: 4px 10px;
                font-weight: 700;
                font-size: 12px;
            }}
            QLabel#stateChip[state="idle"] {{
                background: {chip_idle_bg};
                color: {chip_idle_text};
                border: 1px solid {chip_idle_border};
            }}
            QLabel#stateChip[state="running"] {{
                background: {chip_running_bg};
                color: {chip_running_text};
                border: 1px solid {chip_running_border};
            }}
            QLabel#stateChip[state="cancelling"] {{
                background: {chip_running_bg};
                color: {chip_running_text};
                border: 1px solid {chip_running_border};
            }}
            QLabel#stateChip[state="saving"] {{
                background: {chip_running_bg};
                color: {chip_running_text};
                border: 1px solid {chip_running_border};
            }}
            QLabel#stateChip[state="ready"] {{
                background: {chip_ready_bg};
                color: {chip_ready_text};
                border: 1px solid {chip_ready_border};
            }}
            QLabel#stateChip[state="error"] {{
                background: {chip_error_bg};
                color: {chip_error_text};
                border: 1px solid {chip_error_border};
            }}
            QLabel#mutedChip {{
                background: {chip_muted_bg};
                color: {chip_muted_text};
                border: 1px solid {chip_muted_border};
            }}
            QLabel#emptyStateLabel, QLabel#runningStateLabel {{
                color: {text_secondary};
                font-size: 14px;
                line-height: 1.4em;
                border: 1px dashed {empty_border};
                background: {surface_bg};
                border-radius: 10px;
                padding: 24px;
            }}
            QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background: {input_bg};
                color: {text_primary};
                border: 1px solid {input_border};
                border-radius: 8px;
                padding: 7px 9px;
                selection-background-color: {selection_bg};
                selection-color: {selection_text};
            }}
            QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {focus_border};
            }}
            QTextEdit#summaryViewer, QPlainTextEdit#logViewer {{
                background: {surface_bg};
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 24px;
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                width: 22px;
            }}
            QPushButton {{
                background: {button_bg};
                color: {button_text};
                border: 1px solid {button_border};
                border-radius: 8px;
                padding: 7px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border: 1px solid {button_hover_border};
                background: {button_hover_bg};
            }}
            QPushButton:disabled {{
                color: {text_subtle};
                background: {button_disabled_bg};
                border: 1px solid {button_disabled_border};
            }}
            QPushButton#toolbarButton {{
                min-height: 34px;
                padding-left: 14px;
                padding-right: 14px;
            }}
            QPushButton#primaryRunButton {{
                background: {primary_button_bg};
                color: {primary_button_text};
                border: 1px solid {primary_button_border};
                min-height: 34px;
                padding-left: 16px;
                padding-right: 16px;
            }}
            QPushButton#primaryRunButton:hover {{
                background: {primary_button_hover_bg};
            }}
            QCheckBox {{
                color: {text_primary};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {input_border};
                background: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background: {focus_border};
                border: 1px solid {focus_border};
            }}
            QTabWidget::pane {{
                border: 1px solid {surface_border};
                background: {surface_bg};
                border-radius: 10px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {tab_bg};
                color: {text_secondary};
                border: 1px solid {surface_border};
                border-radius: 8px;
                padding: 9px 14px;
                margin-right: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {tab_selected_bg};
                border: 1px solid {focus_border};
                color: {tab_selected_text};
            }}
            QHeaderView::section {{
                background: {table_header_bg};
                color: {text_primary};
                border: none;
                border-bottom: 1px solid {surface_border};
                padding: 8px 8px;
                font-weight: 700;
            }}
            QTableWidget {{
                background: {surface_bg};
                border: 1px solid {surface_border};
                border-radius: 10px;
                gridline-color: {table_grid};
                alternate-background-color: {table_alt_bg};
                selection-background-color: {selection_bg};
                selection-color: {selection_text};
            }}
            QTableWidget::item {{
                padding: 7px 6px;
            }}
            QTableWidget::item:hover {{
                background: {table_hover_bg};
            }}
        """.format_map(palette)
        self.setStyleSheet(stylesheet)

    def _load_theme_mode(self) -> str:
        saved = str(self.settings.value("theme_mode", "light") or "light").strip().lower()
        return saved if saved in {"light", "dark"} else "light"

    def _sync_theme_toggle(self) -> None:
        if not hasattr(self, "dark_mode_check"):
            return
        self.dark_mode_check.blockSignals(True)
        self.dark_mode_check.setChecked(self.theme_mode == "dark")
        self.dark_mode_check.blockSignals(False)

    def _on_dark_mode_toggled(self, checked: bool) -> None:
        self.theme_mode = "dark" if checked else "light"
        self.settings.setValue("theme_mode", self.theme_mode)
        self._apply_styles()

    def _theme_palette(self) -> dict[str, str]:
        if self.theme_mode == "dark":
            return {
                "window_bg": "#0B1220",
                "surface_bg": "#111827",
                "metric_bg": "#0F1A2B",
                "surface_border": "#253246",
                "splitter_handle": "#253246",
                "text_primary": "#E5EEF9",
                "text_secondary": "#CBD5E1",
                "text_muted": "#94A3B8",
                "text_subtle": "#8FA2BA",
                "chip_idle_bg": "#1E3A5F",
                "chip_idle_text": "#BFDBFE",
                "chip_idle_border": "#3B82F6",
                "chip_running_bg": "#4C3314",
                "chip_running_text": "#FCD34D",
                "chip_running_border": "#D97706",
                "chip_ready_bg": "#123524",
                "chip_ready_text": "#86EFAC",
                "chip_ready_border": "#22C55E",
                "chip_error_bg": "#4C1D1D",
                "chip_error_text": "#FCA5A5",
                "chip_error_border": "#EF4444",
                "chip_muted_bg": "#172033",
                "chip_muted_text": "#CBD5E1",
                "chip_muted_border": "#314158",
                "empty_border": "#334155",
                "input_bg": "#0F172A",
                "input_border": "#334155",
                "focus_border": "#22D3EE",
                "button_bg": "#172033",
                "button_text": "#E5EEF9",
                "button_border": "#334155",
                "button_hover_border": "#475569",
                "button_hover_bg": "#1E293B",
                "button_disabled_bg": "#101827",
                "button_disabled_border": "#253246",
                "primary_button_bg": "#0E7490",
                "primary_button_text": "#FFFFFF",
                "primary_button_border": "#22D3EE",
                "primary_button_hover_bg": "#155E75",
                "tab_bg": "#172033",
                "tab_selected_bg": "#111827",
                "tab_selected_text": "#93C5FD",
                "table_header_bg": "#182235",
                "table_grid": "#253246",
                "table_alt_bg": "#0F172A",
                "selection_bg": "#155E75",
                "selection_text": "#F8FAFC",
                "table_hover_bg": "#172554",
            }
        return {
            "window_bg": "#F3F5F7",
            "surface_bg": "#FFFFFF",
            "metric_bg": "#FBFCFD",
            "surface_border": "#DDE3EA",
            "splitter_handle": "#D3DCE5",
            "text_primary": "#1F2937",
            "text_secondary": "#4B5563",
            "text_muted": "#6B7280",
            "text_subtle": "#8A97A6",
            "chip_idle_bg": "#E0F2FE",
            "chip_idle_text": "#075985",
            "chip_idle_border": "#7DD3FC",
            "chip_running_bg": "#FEF3C7",
            "chip_running_text": "#92400E",
            "chip_running_border": "#FCD34D",
            "chip_ready_bg": "#DCFCE7",
            "chip_ready_text": "#166534",
            "chip_ready_border": "#86EFAC",
            "chip_error_bg": "#FEE2E2",
            "chip_error_text": "#991B1B",
            "chip_error_border": "#FCA5A5",
            "chip_muted_bg": "#F4F7FA",
            "chip_muted_text": "#4B5563",
            "chip_muted_border": "#DDE3EA",
            "empty_border": "#CAD5DF",
            "input_bg": "#FFFFFF",
            "input_border": "#CAD5DF",
            "focus_border": "#0F8FA3",
            "button_bg": "#FFFFFF",
            "button_text": "#1F2937",
            "button_border": "#CAD5DF",
            "button_hover_border": "#B4C2CF",
            "button_hover_bg": "#F6F9FC",
            "button_disabled_bg": "#F4F7FA",
            "button_disabled_border": "#E3EAF1",
            "primary_button_bg": "#0F8FA3",
            "primary_button_text": "#FFFFFF",
            "primary_button_border": "#0C7485",
            "primary_button_hover_bg": "#0C7485",
            "tab_bg": "#F6F9FC",
            "tab_selected_bg": "#FFFFFF",
            "tab_selected_text": "#0F8FA3",
            "table_header_bg": "#F5F8FB",
            "table_grid": "#E7EDF3",
            "table_alt_bg": "#FBFCFD",
            "selection_bg": "#D9F4F7",
            "selection_text": "#1F2937",
            "table_hover_bg": "#F1F7FB",
        }

    def _set_idle_state(self) -> None:
        self.state_mode = "idle"
        self.last_error_message = ""
        self.last_save_error_message = ""
        self.last_save_failed = False
        self._update_state_chip(state="idle", text=self.tr("state_idle"))
        self.secondary_chip.setText(self.tr("secondary_no_results"))
        self.left_state_hint.setText(self.tr("idle_hint"))
        self.result_stack.setCurrentIndex(0)
        self._set_scan_inputs_enabled(True)
        self.result_selector.setEnabled(False)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_again_button.setEnabled(False)

    def _set_running_state(self) -> None:
        self.state_mode = "running"
        self.last_error_message = ""
        self.last_save_error_message = ""
        self.last_save_failed = False
        self._update_state_chip(state="running", text=self.tr("state_running"))
        self.secondary_chip.setText(self.tr("secondary_scanning"))
        self.left_state_hint.setText(self.tr("running_hint"))
        self.result_stack.setCurrentIndex(2)
        self.tab_widget.setCurrentWidget(self.summary_text)
        self._set_scan_inputs_enabled(False)
        self.result_selector.setEnabled(False)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_again_button.setEnabled(False)

    def _set_cancelling_state(self) -> None:
        self.state_mode = "cancelling"
        self._update_state_chip(state="cancelling", text=self.tr("state_cancelling"))
        self.secondary_chip.setText(self.tr("secondary_stopping"))
        self.left_state_hint.setText(self.tr("cancelling_hint"))
        self.result_stack.setCurrentIndex(2)
        self.tab_widget.setCurrentWidget(self.summary_text)
        self._set_scan_inputs_enabled(False)
        self.result_selector.setEnabled(False)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_again_button.setEnabled(False)

    def _set_saving_state(self) -> None:
        self.state_mode = "saving"
        self.last_error_message = ""
        self.last_save_error_message = ""
        self.last_save_failed = False
        self._update_state_chip(state="saving", text=self.tr("state_saving"))
        self.secondary_chip.setText(self.tr("secondary_saving"))
        self.left_state_hint.setText(self.tr("saving_hint"))
        self.result_stack.setCurrentIndex(2)
        self._set_scan_inputs_enabled(False)
        self.result_selector.setEnabled(bool(self.batch_result and self.batch_result.get("results")))
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_again_button.setEnabled(False)

    def _set_result_ready_state(self, message: str) -> None:
        self.state_mode = "ready"
        self.last_error_message = ""
        self.last_save_error_message = ""
        self.last_save_failed = False
        self._update_state_chip(state="ready", text=self.tr("state_ready"))
        self.secondary_chip.setText(self.tr("secondary_ready"))
        self.left_state_hint.setText(message)
        self.result_stack.setCurrentIndex(2)
        self._set_scan_inputs_enabled(True)
        self.result_selector.setEnabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_again_button.setEnabled(True)

    def _set_error_state(self, message: str) -> None:
        self.state_mode = "error"
        self.last_error_message = message
        self._update_state_chip(state="error", text=self.tr("state_error"))
        self.secondary_chip.setText(self.tr("secondary_failed"))
        self.left_state_hint.setText(message)
        self._set_scan_inputs_enabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_again_button.setEnabled(self.batch_result is not None)
        if self.batch_result and self.batch_result.get("results"):
            self.result_stack.setCurrentIndex(2)
            self.result_selector.setEnabled(True)
        else:
            self.result_stack.setCurrentIndex(0)
            self.result_selector.setEnabled(False)

    def _update_state_chip(self, state: str, text: str) -> None:
        self.state_chip.setProperty("state", state)
        self.state_chip.setText(text)
        self.state_chip.style().unpolish(self.state_chip)
        self.state_chip.style().polish(self.state_chip)

    def _reset_result_views(self) -> None:
        self.result_selector.clear()
        self._set_current_target("-")
        self._set_current_output("-")
        self.summary_text.clear()
        self._set_summary_card(self.card_js_value, 0)
        self._set_summary_card(self.card_page_value, 0)
        self._set_summary_card(self.card_api_value, 0)
        self._set_summary_card(self.card_recursive_value, 0)
        self._set_summary_card(self.card_sensitive_total_value, 0)
        self._set_summary_card(self.card_sensitive_high_value, 0)
        self.js_rows = []
        self.page_rows = []
        self.api_rows = []
        self.sensitive_records = []
        if hasattr(self, "sensitive_type_combo"):
            self.sensitive_type_combo.setCurrentIndex(0)
        self._populate_table(self.js_table, [])
        self._populate_table(self.page_table, [])
        self._populate_table(self.api_table, [])
        self._populate_table(self.sensitive_table, [])
        self._update_filter_count(self.js_count_label, 0, 0)
        self._update_filter_count(self.page_count_label, 0, 0)
        self._update_filter_count(self.api_count_label, 0, 0)
        self._update_filter_count(self.sensitive_count_label, 0, 0)

    def _build_ready_message(self, batch_result: dict) -> str:
        result_count = len(batch_result.get("results", []))
        success_count = _safe_int(batch_result.get("success_count", 0), 0)
        return self.tr(
            "scan_complete_message",
            count=result_count,
            success=success_count,
            failed=result_count - success_count,
        )

    def _get_save_output_path(self, prefer_typed_output: bool = False) -> Optional[Path]:
        typed_output = self.output_input.text().strip() if hasattr(self, "output_input") else ""
        if prefer_typed_output and typed_output:
            chosen_path = Path(typed_output)
            if chosen_path.suffix.lower() in {".xlsx", ".html"}:
                chosen_path = chosen_path.with_suffix("")
            self.output_input.setText(str(chosen_path))
            return chosen_path

        default_path = Path(self.default_output_path or "discovery-result")
        if default_path.suffix.lower() in {".xlsx", ".html"}:
            default_path = default_path.with_suffix("")
        default = str(default_path)
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("save_dialog_title"),
            default,
            self.tr("save_dialog_filter"),
        )
        if not chosen:
            return None
        chosen_path = Path(chosen)
        if chosen_path.suffix.lower() in {".xlsx", ".html"}:
            chosen_path = chosen_path.with_suffix("")
        return chosen_path

    def choose_output_file(self) -> None:
        default_path = Path(self.output_input.text().strip() or self.default_output_path or "discovery-result")
        if default_path.suffix.lower() in {".xlsx", ".html"}:
            default_path = default_path.with_suffix("")
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("save_output_file"),
            str(default_path),
            self.tr("save_dialog_filter"),
        )
        if not chosen:
            return
        chosen_path = Path(chosen)
        if chosen_path.suffix.lower() in {".xlsx", ".html"}:
            chosen_path = chosen_path.with_suffix("")
        self.output_input.setText(str(chosen_path))
        self.default_output_path = str(chosen_path)

    def choose_js_output_dir(self) -> None:
        default = self.js_output_dir_input.text().strip() or str(Path.cwd())
        chosen = QFileDialog.getExistingDirectory(
            self,
            self.tr("choose_js_output_dir"),
            default,
        )
        if chosen:
            self.js_output_dir_input.setText(chosen)

    def _focus_options_panel(self) -> None:
        self.left_scroll.ensureWidgetVisible(self.option_card, 0, 24)
        self.max_js_spin.setFocus(Qt.FocusReason.OtherFocusReason)

    def _save_log(self) -> None:
        default = str(Path(self.default_output_path or "discovery-result").with_suffix(".log"))
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("save_log_title"),
            default,
            self.tr("save_log_filter"),
        )
        if not chosen:
            return
        try:
            Path(chosen).write_text(self.log_text.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, self.tr("save_error_title"), self.tr("save_error_body", message=str(exc)))

    def run_scan(self) -> None:
        if self.worker_thread is not None:
            QMessageBox.information(self, self.tr("scan_in_progress_title"), self.tr("scan_in_progress_body"))
            return
        if self.save_thread is not None:
            QMessageBox.information(self, self.tr("save_in_progress_title"), self.tr("save_in_progress_body"))
            return

        try:
            urls = parse_input_urls(self.url_input.toPlainText())
            headers = parse_header_lines(self.header_input.toPlainText())
            excluded_subdomains = parse_hostname_filters([self.excluded_subdomains_input.text()])
            js_output_dir_raw = self.js_output_dir_input.text().strip()
            request = ScanRequest(
                urls=urls,
                config=Config(
                    url=urls[0],
                    max_js_files=self.max_js_spin.value(),
                    max_depth=self.max_depth_spin.value(),
                    timeout=self.timeout_spin.value(),
                    output=Path("discovery-result.json"),
                    skip_probe=self.skip_probe_check.isChecked(),
                    recursive_scan=self.recursive_scan_check.isChecked(),
                    recursive_depth=self.recursive_depth_spin.value(),
                    include_subdomains=self.include_subdomains_check.isChecked(),
                    excluded_subdomains=excluded_subdomains,
                    max_workers=self.max_workers_spin.value(),
                    request_delay=self.request_delay_spin.value(),
                    headers=headers,
                    verify_ssl=self.verify_ssl_check.isChecked(),
                    proxy_url=self.proxy_input.text().strip(),
                    js_output_dir=Path(js_output_dir_raw) if js_output_dir_raw else None,
                ),
            )
            validate_config(request.config)
        except Exception as exc:
            QMessageBox.critical(self, self.tr("input_error_title"), str(exc))
            return

        if not request.config.verify_ssl:
            QMessageBox.warning(
                self,
                self.tr("security_warning_title"),
                self.tr("security_warning_body"),
            )

        self.log_text.clear()
        self.batch_result = None
        self.current_output_path = ""
        self._reset_result_views()

        self.worker_thread = QThread(self)
        self.worker = ScanWorker(request)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.cancelled.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.cancelled.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self._cleanup_worker)

        if not request.config.verify_ssl:
            self.log_text.appendPlainText(self.tr("log_ssl_warning"))
        self._set_running_state()
        self.worker_thread.start()

    def cancel_scan(self) -> None:
        if self.worker is None or self.worker_thread is None:
            QMessageBox.information(self, self.tr("no_scan_title"), self.tr("no_scan_body"))
            return
        if self.worker.is_cancel_requested():
            return
        self.worker.cancel()
        self.log_text.appendPlainText(self.tr("log_cancel_requested"))
        self._set_cancelling_state()

    def _on_progress(self, message: str) -> None:
        self.log_text.appendPlainText(message)

    def _on_finished(self, batch_result: dict) -> None:
        self.batch_result = batch_result
        self.current_output_path = ""
        self.current_output_save_failed = False
        self.last_save_failed = False
        self.last_save_error_message = ""
        self._set_current_output("")
        self._refresh_result_selector()
        self._set_result_ready_state(self._build_ready_message(batch_result))

    def _on_failed(self, message: str) -> None:
        self.last_save_failed = False
        self.log_text.appendPlainText(self.tr("log_error", message=message))
        self._set_error_state(message)
        QMessageBox.critical(self, self.tr("execution_error_title"), message)

    def _on_save_finished(self, output_paths: object) -> None:
        saved_paths = tuple(output_paths) if isinstance(output_paths, (list, tuple)) else ()
        output_label = format_export_output_label([Path(path) for path in saved_paths]) if saved_paths else ""
        selected_index = self.result_selector.currentIndex()
        self.current_output_path = output_label
        if saved_paths:
            self.default_output_path = str(Path(saved_paths[0]).with_suffix(""))
            if hasattr(self, "output_input"):
                self.output_input.setText(self.default_output_path)
        self.current_output_save_failed = False
        self.last_save_failed = False
        self.last_save_error_message = ""
        self.log_text.appendPlainText(self.tr("log_save_completed", path=output_label))
        self._set_current_output(output_label)
        self._refresh_result_selector(selected_index=selected_index)
        if self.batch_result:
            self._set_result_ready_state(self._build_ready_message(self.batch_result))

    def _on_save_failed(self, message: str) -> None:
        selected_index = self.result_selector.currentIndex()
        self.current_output_path = ""
        self.last_save_failed = True
        self.last_save_error_message = message
        self.log_text.appendPlainText(self.tr("log_save_error", message=message))
        self._set_current_output("", save_failed=True)
        self._refresh_result_selector(selected_index=selected_index)
        batch_result = self.batch_result or {}
        result_count = len(batch_result.get("results", []))
        success_count = _safe_int(batch_result.get("success_count", 0), 0)
        self._set_error_state(self.tr("save_failed_state", message=message))
        self.left_state_hint.setText(
            self.tr(
                "save_failed_hint",
                count=result_count,
                success=success_count,
                failed=result_count - success_count,
            )
        )
        QMessageBox.critical(self, self.tr("save_error_title"), self.tr("save_error_body", message=message))

    def _on_cancelled(self, message: str) -> None:
        self.log_text.appendPlainText(self.tr("log_cancelled", message=message))
        self.batch_result = None
        self.current_output_path = ""
        self.last_save_failed = False
        self.last_save_error_message = ""
        self._reset_result_views()
        self._set_idle_state()
        self.left_state_hint.setText(message)

    def _cleanup_worker(self) -> None:
        self.worker = None
        self.worker_thread = None

    def _cleanup_save_worker(self) -> None:
        self.save_worker = None
        self.save_thread = None

    def save_results(self) -> None:
        if not self.batch_result:
            QMessageBox.information(self, self.tr("no_results_title"), self.tr("no_results_body"))
            return
        if self.save_thread is not None:
            QMessageBox.information(self, self.tr("save_in_progress_title"), self.tr("save_in_progress_body"))
            return

        output_path = self._get_save_output_path(prefer_typed_output=True)
        if output_path is None:
            return
        self.default_output_path = str(output_path)
        self.save_thread = QThread(self)
        self.save_worker = SaveWorker(output_path, self.batch_result)
        self.save_worker.moveToThread(self.save_thread)
        self.save_thread.started.connect(self.save_worker.run)
        self.save_worker.finished.connect(self._on_save_finished)
        self.save_worker.failed.connect(self._on_save_failed)
        self.save_worker.finished.connect(self.save_worker.deleteLater)
        self.save_worker.failed.connect(self.save_worker.deleteLater)
        self.save_worker.finished.connect(self.save_thread.quit)
        self.save_worker.failed.connect(self.save_thread.quit)
        self.save_thread.finished.connect(self.save_thread.deleteLater)
        self.save_thread.finished.connect(self._cleanup_save_worker)
        self._set_saving_state()
        self.save_thread.start()

    def _refresh_result_selector(self, selected_index: Optional[int] = None) -> None:
        self.result_selector.blockSignals(True)
        self.result_selector.clear()
        if not self.batch_result:
            self.result_selector.blockSignals(False)
            self._set_idle_state()
            return
        records = self.batch_result.get("results", [])
        for index, record in enumerate(records, start=1):
            status = record.get("status", "unknown")
            url = record.get("input_url", "-")
            self.result_selector.addItem(
                self.tr("result_selector_item", index=index, status=_scan_status_text(status, self.ui_language), url=url)
            )
        self.result_selector.blockSignals(False)
        self.result_selector.setEnabled(bool(records))
        if records:
            next_index = 0 if selected_index is None else max(0, min(selected_index, len(records) - 1))
            self.result_selector.setCurrentIndex(next_index)
            self._on_result_changed(next_index)
        else:
            self._set_idle_state()

    def _on_result_changed(self, index: int) -> None:
        if not self.batch_result:
            return
        records = self.batch_result.get("results", [])
        if index < 0 or index >= len(records):
            return
        self._update_for_selected_result(records[index])

    def _update_for_selected_result(self, result: dict) -> None:
        target = result.get("input_url", "-")
        self._set_current_target(target)

        status = str(result.get("status", "unknown"))
        if status == "success":
            self.secondary_chip.setText(self.tr("secondary_selected_success"))
        else:
            self.secondary_chip.setText(self.tr("secondary_selected_failed"))

        summary = result.get("summary") or {}
        self._set_summary_card(self.card_js_value, self._summary_count(summary, "js_fetched", len(result.get("js_files") or [])))
        self._set_summary_card(self.card_page_value, self._summary_count(summary, "page_count", len(self._page_items(result))))
        self._set_summary_card(self.card_api_value, self._summary_count(summary, "api_count", len(self._api_items(result))))
        self._set_summary_card(self.card_recursive_value, result.get("recursive_total_scans", 0))
        sensitive_total, sensitive_high = self._resolve_sensitive_metrics(result, summary)
        self._set_summary_card(self.card_sensitive_total_value, sensitive_total)
        self._set_summary_card(self.card_sensitive_high_value, sensitive_high)

        if self.batch_result and len(self.batch_result.get("results", [])) > 1:
            summary_text = build_batch_summary_text(
                self.batch_result,
                result,
                self._summary_output_path(),
                language=self.ui_language,
            )
        else:
            summary_text = build_summary_text(
                result,
                self._summary_output_path(),
                language=self.ui_language,
            )
        self.summary_text.setPlainText(summary_text)
        self._rebuild_tables(result)
        self.result_stack.setCurrentIndex(2)

    def _summary_output_path(self) -> Path | str:
        if self.current_output_path:
            return self.current_output_path
        if self.last_save_failed:
            return self.tr("output_save_failed")
        if self.batch_result:
            return self.tr("output_not_saved")
        return "-"

    def _set_summary_card(self, label: QLabel, value: object) -> None:
        label.setText(str(_safe_int(value, 0)))

    def _summary_count(self, summary: dict, key: str, fallback: int) -> int:
        value = _safe_int(summary.get(key, 0), 0)
        return value or fallback

    def _update_filter_count(self, label: QLabel, visible: int, total: int) -> None:
        label.setText(self.tr("count_label", visible=visible, total=total))

    def _extract_sensitive_findings(self, result: dict) -> List[dict]:
        sensitive_raw = result.get("sensitive_findings")
        hardcoded_raw = result.get("hardcoded_findings")
        sensitive = [item for item in sensitive_raw if isinstance(item, dict)] if isinstance(sensitive_raw, list) else []
        hardcoded = [item for item in hardcoded_raw if isinstance(item, dict)] if isinstance(hardcoded_raw, list) else []
        if sensitive and hardcoded:
            return sensitive + [item for item in hardcoded if item not in sensitive]
        if sensitive:
            return sensitive
        if hardcoded:
            return hardcoded
        return []

    def _resolve_sensitive_metrics(self, result: dict, summary: dict) -> Tuple[int, int]:
        findings = self._extract_sensitive_findings(result)
        total = _safe_int(
            summary.get("sensitive_total", summary.get("hardcoded_total", len(findings))),
            len(findings),
        )
        high_default = sum(
            1
            for item in findings
            if self._extract_sensitive_severity(item) in {"high", "critical"}
        )
        high = _safe_int(
            summary.get(
                "sensitive_high",
                summary.get("sensitive_high_or_above", summary.get("hardcoded_high_or_above", high_default)),
            ),
            high_default,
        )
        return total, high

    def _extract_sensitive_severity(self, item: dict) -> str:
        classification = item.get("classification")
        if isinstance(classification, dict):
            value = classification.get("risk_level", item.get("severity"))
        else:
            value = item.get("severity")
        return _normalize_sensitive_severity(value)

    def _extract_sensitive_type(self, item: dict) -> Tuple[str, str]:
        classification = item.get("classification")
        if isinstance(classification, dict):
            raw_type = (
                item.get("type")
                or item.get("category")
                or classification.get("entity_type")
                or classification.get("subtype")
                or item.get("subtype")
                or ""
            )
        else:
            raw_type = item.get("type") or item.get("category") or item.get("subtype") or ""
        canonical = _normalize_sensitive_type(raw_type)
        return canonical, str(raw_type or canonical)

    def _sensitive_type_text(self, canonical_type: str, raw_type: str) -> str:
        key_map = {
            "email": "sensitive_type_email",
            "phone": "sensitive_type_phone",
            "name": "sensitive_type_name",
            "account": "sensitive_type_account",
            "credential": "sensitive_type_credential",
            "token": "sensitive_type_token",
            "user_id": "sensitive_type_user_id",
            "other": "sensitive_type_other",
        }
        if canonical_type in key_map:
            return self.tr(key_map[canonical_type])
        return raw_type or self.tr("sensitive_type_other")

    def _extract_sensitive_source(self, item: dict) -> str:
        source_kind = str(item.get("source_kind") or item.get("source_type") or "").strip()
        source_label = str(
            item.get("source_label")
            or item.get("source_url")
            or item.get("source_path")
            or item.get("url")
            or ""
        ).strip()
        if source_kind and source_label:
            return f"{source_kind} | {source_label}"
        if source_label:
            return source_label
        if source_kind:
            return source_kind
        return "-"

    def _extract_sensitive_location(self, item: dict) -> str:
        label = str(item.get("location_label") or "").strip()
        if label:
            return label

        location = item.get("location")
        if isinstance(location, dict):
            line = location.get("line")
            column = location.get("column")
            if line is not None and column is not None:
                return f"line {line}, col {column}"
            if line is not None:
                return f"line {line}"
            block_index = location.get("block_index")
            if block_index is not None:
                return f"block #{block_index}"
            start = location.get("offset_start")
            end = location.get("offset_end")
            if start is not None and end is not None:
                return f"offset {start}-{end}"

        line = item.get("line")
        column = item.get("column")
        if line is not None and column is not None:
            return f"line {line}, col {column}"
        if line is not None:
            return f"line {line}"
        return "-"

    def _extract_sensitive_confidence(self, item: dict) -> str:
        classification = item.get("classification")
        if isinstance(classification, dict):
            raw = classification.get("confidence", item.get("confidence"))
        else:
            raw = item.get("confidence")
        if raw is None:
            return "-"
        score = _safe_float(raw, -1.0)
        if score < 0:
            return "-"
        if score > 1:
            return f"{score:.1f}%"
        return f"{score:.2f}"

    def _extract_sensitive_display_value(self, item: dict) -> str:
        raw = item.get("value", item.get("raw_value"))
        if raw is not None and str(raw).strip():
            return str(raw).strip()
        masked = item.get("masked_value")
        if masked is None:
            masked = item.get("maskedValue")
        if masked is not None and str(masked).strip():
            return str(masked).strip()
        return "-"

    def _extract_sensitive_records(self, result: dict) -> List[dict]:
        records: List[dict] = []
        for item in self._extract_sensitive_findings(result):
            canonical_type, raw_type = self._extract_sensitive_type(item)
            severity = self._extract_sensitive_severity(item)
            display_type = self._sensitive_type_text(canonical_type, raw_type)
            display_value = self._extract_sensitive_display_value(item)
            confidence_text = self._extract_sensitive_confidence(item)
            source_text = self._extract_sensitive_source(item)
            location_text = self._extract_sensitive_location(item)
            records.append(
                {
                    "type": canonical_type,
                    "severity": severity,
                    "row": (
                        display_type,
                        display_value,
                        confidence_text,
                        severity,
                        source_text,
                        location_text,
                    ),
                }
            )
        return records

    def _api_items(self, result: dict) -> List[dict]:
        items: List[dict] = []
        seen: set[str] = set()
        for key, accessible_default in (
            ("all_apis", None),
            ("accessible_apis", True),
            ("probe_results", None),
        ):
            for item in result.get(key) or []:
                if not isinstance(item, dict):
                    continue
                identity = str(item.get("url") or item.get("path") or item.get("endpoint") or "")
                if not identity:
                    identity = repr(sorted(item.items()))
                if identity in seen:
                    continue
                seen.add(identity)
                normalized = dict(item)
                if accessible_default is not None and "accessible" not in normalized:
                    normalized["accessible"] = accessible_default
                items.append(normalized)
        return items

    def _api_source_text(self, item: dict) -> str:
        sources = item.get("sources")
        if isinstance(sources, (list, tuple, set)):
            return ", ".join(str(source) for source in sources)
        if sources:
            return str(sources)
        return str(item.get("source") or "")

    def _page_items(self, result: dict) -> List[dict]:
        items: List[dict] = []
        seen: set[str] = set()
        for key, accessible_default in (
            ("all_pages", None),
            ("accessible_pages", True),
        ):
            for item in result.get(key) or []:
                if not isinstance(item, dict):
                    continue
                identity = str(item.get("url") or item.get("path") or "")
                if not identity:
                    identity = repr(sorted(item.items()))
                if identity in seen:
                    continue
                seen.add(identity)
                normalized = dict(item)
                if accessible_default is not None and "accessible" not in normalized:
                    normalized["accessible"] = accessible_default
                items.append(normalized)
        return items

    def _sensitive_record_matches_search(self, record: dict, filter_column: Optional[str], filter_text: str) -> bool:
        keyword = filter_text.strip().casefold()
        if not keyword:
            return True

        row = record.get("row") or ()
        columns = self._localized_headers(SENSITIVE_HEADER_KEYS)
        if not filter_column:
            target_indexes = range(len(row))
        else:
            try:
                target_indexes = [columns.index(filter_column)]
            except ValueError:
                target_indexes = range(len(row))
        for index in target_indexes:
            if index >= len(row):
                continue
            if keyword in str(row[index]).casefold():
                return True
        return False

    def _rebuild_tables(self, result: dict) -> None:
        self.sensitive_records = self._extract_sensitive_records(result)

        self.js_rows = []
        for item in result.get("js_files", []):
            self.js_rows.append(
                (
                    str(item.get("depth", "")),
                    _status_text(item.get("status_code")),
                    self.tr("yes") if item.get("success") else self.tr("no"),
                    str(item.get("length", "")),
                    str(item.get("saved_path", "") or ""),
                    str(item.get("save_error", "") or ""),
                    str(item.get("error", "") or ""),
                    str(item.get("url", "") or ""),
                )
            )

        self.page_rows = []
        for item in self._page_items(result):
            self.page_rows.append(
                (
                    _status_text(item.get("status_code")),
                    str(item.get("length", "")),
                    _accessible_text(item.get("accessible"), self.ui_language),
                    str(item.get("probe_method", "") or ""),
                    str(item.get("path", "") or ""),
                    self._api_source_text(item),
                    str(item.get("url", "") or ""),
                )
            )

        self.api_rows = []
        for item in self._api_items(result):
            self.api_rows.append(
                (
                    _status_text(item.get("status_code")),
                    _accessible_text(item.get("accessible"), self.ui_language),
                    str(item.get("probe_method") or item.get("method") or ""),
                    str(item.get("path") or item.get("endpoint") or ""),
                    self._api_source_text(item),
                    str(item.get("url", "") or ""),
                )
            )

        self._apply_sensitive_filters()
        self._apply_js_filters()
        self._apply_page_filters()
        self._apply_api_filters()

    def _apply_sensitive_filters(self) -> None:
        filter_column = None if self.sensitive_filter_col.currentIndex() == 0 else self.sensitive_filter_col.currentText()
        filter_text = self.sensitive_filter_text.text()
        selected_type = str(self.sensitive_type_combo.currentData() or "all")

        records = [
            record
            for record in self.sensitive_records
            if self._sensitive_record_matches_search(record, filter_column, filter_text)
        ]
        if self.sensitive_high_only_check.isChecked():
            records = [record for record in records if record.get("severity") in {"high", "critical"}]
        if selected_type != "all":
            records = [record for record in records if record.get("type") == selected_type]

        rows = [record.get("row", ()) for record in records]
        self._update_filter_count(self.sensitive_count_label, len(rows), len(self.sensitive_records))
        self._populate_table(self.sensitive_table, rows)

    def _apply_js_filters(self) -> None:
        filter_column = None if self.js_filter_col.currentIndex() == 0 else self.js_filter_col.currentText()
        rows = filter_table_rows(
            rows=self.js_rows,
            columns=self._localized_headers(JS_HEADER_KEYS),
            filter_column=filter_column,
            filter_text=self.js_filter_text.text(),
        )
        if self.js_success_only_check.isChecked():
            rows = [row for row in rows if row[2] == self.tr("yes")]
        self._update_filter_count(self.js_count_label, len(rows), len(self.js_rows))
        self._populate_table(self.js_table, rows)

    def _apply_page_filters(self) -> None:
        filter_column = None if self.page_filter_col.currentIndex() == 0 else self.page_filter_col.currentText()
        rows = filter_table_rows(
            rows=self.page_rows,
            columns=self._localized_headers(PAGE_HEADER_KEYS),
            filter_column=filter_column,
            filter_text=self.page_filter_text.text(),
        )
        if self.page_accessible_only_check.isChecked():
            rows = [row for row in rows if row[2] == self.tr("yes")]
        if self.page_status_200_check.isChecked():
            rows = [row for row in rows if row[0] == "200"]
        self._update_filter_count(self.page_count_label, len(rows), len(self.page_rows))
        self._populate_table(self.page_table, rows)

    def _apply_api_filters(self) -> None:
        filter_column = None if self.api_filter_col.currentIndex() == 0 else self.api_filter_col.currentText()
        rows = filter_table_rows(
            rows=self.api_rows,
            columns=self._localized_headers(RESULT_HEADER_KEYS),
            filter_column=filter_column,
            filter_text=self.api_filter_text.text(),
        )
        if self.api_accessible_only_check.isChecked():
            rows = [row for row in rows if row[1] == self.tr("yes")]
        if self.api_status_200_check.isChecked():
            rows = [row for row in rows if row[0] == "200"]
        self._update_filter_count(self.api_count_label, len(rows), len(self.api_rows))
        self._populate_table(self.api_table, rows)

    def _populate_table(self, table: QTableWidget, rows: List[Tuple[str, ...]]) -> None:
        table.setSortingEnabled(False)
        try:
            table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                for col_index, value in enumerate(row):
                    text = str(value)
                    item = SortableTableWidgetItem(text)
                    sort_value = _table_sort_value(text)
                    if sort_value is not None:
                        item.setData(Qt.ItemDataRole.UserRole, sort_value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    item.setToolTip(text)
                    table.setItem(row_index, col_index, item)
                table.setRowHeight(row_index, 28)
        finally:
            table.setSortingEnabled(True)

    def _on_table_double_click(self, table: QTableWidget, row: int, col: int) -> None:
        item = table.item(row, col)
        if item is None:
            return
        value = item.text()
        QGuiApplication.clipboard().setText(value)
        dialog = CellDetailDialog(value, language=self.ui_language, parent=self)
        dialog.exec()


def run_qt_gui(
    initial_url: Optional[str] = None,
    initial_output: Optional[str] = None,
    initial_js_output_dir: Optional[str] = None,
) -> int:
    app = QApplication.instance() or QApplication([])
    window = DiscoveryWindow(
        initial_url=initial_url,
        initial_output=initial_output,
        initial_js_output_dir=initial_js_output_dir,
    )
    window.show()
    return app.exec()
