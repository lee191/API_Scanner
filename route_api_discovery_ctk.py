#!/usr/bin/env python3
"""CustomTkinter GUI for route_api_discovery — redesigned to match Precision Workbench layout."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from route_api_discovery import (
    CANCEL_MESSAGE,
    Config,
    ScanCancelled,
    build_execution_context,
    discover_many,
    parse_header_entry,
    parse_header_lines,
    parse_hostname_filters,
    parse_input_urls,
    resolve_sensitive_findings,
    save_export_bundle,
    validate_config,
)

# ── Palette ───────────────────────────────────────────────────────────────────

LIGHT = dict(
    window="#F3F5F7", surface="#FFFFFF", surface2="#F8FAFC",
    border="#CBD5E1", border2="#94A3B8",
    text="#111827", text2="#374151", muted="#4B5563", subtle="#64748B",
    disabled_bg="#EEF2F6", disabled_fg="#7A869A", border_disabled="#CBD5E1",
    action_bg="#0F8FA3", action_hover="#0C7485", action_text="#FFFFFF",
    accent="#0F8FA3", accent_dark="#0C7485",
    chip_bg="#E0F2FE", chip_fg="#075985",
    badge_idle="#E0F2FE", badge_idle_fg="#075985",
    badge_run="#FEF3C7",  badge_run_fg="#92400E",
    badge_save="#DBEAFE", badge_save_fg="#1E40AF",
    badge_done="#DCFCE7", badge_done_fg="#166534",
    badge_err="#FEE2E2",  badge_err_fg="#991B1B",
    m_summary="#475569", m_success="#16A34A", m_sensitive="#DC2626", m_js="#2563EB",
    m_pages="#7C3AED",   m_apis="#0891B2",
    row_alt="#F1F5F9",   sel_bg="#DBEAFE", sel_fg="#1E40AF",
    tree_header="#E2E8F0",
    field_bg="#F8FAFC", field_border="#94A3B8", field_focus="#0F8FA3",
    table_bg="#FFFFFF", table_header_bg="#E2E8F0", table_row_alt="#F1F5F9",
    table_selected_bg="#DBEAFE", table_selected_fg="#1E40AF",
    tab_selected_bg="#0F8FA3", tab_hover="#E2E8F0",
    method_get="#16A34A", method_post="#2563EB", method_put="#D97706",
    method_patch="#7C3AED", method_del="#DC2626",
    method_head="#0891B2", method_other="#64748B",
    sb_bg="#F1F5F9",
)
def _pal() -> dict:
    return LIGHT


# ── Texts ─────────────────────────────────────────────────────────────────────

KO: Dict[str, str] = {
    "window_title": "Route API Discovery - Precision Workbench",
    "app_title": "Route API Discovery",
    "app_subtitle": "Precision Workbench",
    "run": "▶  실행", "stop": "■  정지", "save_results": "⬇  결과 저장",
    "settings": "⚙  설정",
    "exec_status": "실행 상태",
    "idle": "준비됨", "running": "실행 중", "cancelling": "중지 중",
    "saving": "저장 중", "done": "완료", "error": "오류",
    "target_url": "대상 URL",
    "url_hint": "한 줄에 URL 하나씩 입력",
    "url_help": "여러 대상은 줄바꿈으로 추가하세요. 스캔은 입력 순서대로 실행됩니다.",
    "output_file": "출력 파일 경로",
    "output_hint": "결과 기본 파일명",
    "browse": "찾아보기",
    "request_headers": "요청 헤더",
    "col_name": "이름", "col_value": "값",
    "add": "추가", "edit": "편집", "remove": "삭제", "import_": "가져오기",
    "scan_options": "스캔 옵션",
    "browser_options": "브라우저 분석",
    "recursive_scan": "재귀 스캔",
    "include_subdomains": "서브도메인",
    "skip_probe": "프로브 생략",
    "verify_ssl": "SSL 검증",
    "max_js": "JS 최대",
    "max_depth": "최대 깊이",
    "max_workers": "동시 요청",
    "timeout": "타임아웃(s)",
    "request_delay": "딜레이(s)",
    "recursive_depth": "재귀 단계",
    "advanced_options": "고급 옵션",
    "proxy": "프록시",
    "proxy_hint": "http://127.0.0.1:8080",
    "excluded_sub": "제외 서브도메인",
    "excluded_hint": "예: cdn.example.com",
    "js_dir": "JS 저장 폴더",
    "results": "탐색 결과",
    "m_summary": "스캔", "m_success": "성공",
    "m_js": "JS 파일", "m_pages": "페이지", "m_apis": "API",
    "filter_hint": "경로, 출처, 콘텐츠 유형 검색",
    "quantity": "표시 개수", "url_type": "메서드",
    "status_code": "상태 코드",
    "all": "전체", "reset": "초기화",
    "col_method": "메서드", "col_endpoint": "엔드포인트",
    "col_source": "출처", "col_status": "상태 코드",
    "col_params": "파라미터", "col_sensitive": "민감정보",
    "col_severity": "심각도", "col_ctype": "콘텐츠 유형",
    "col_accessible": "접근",
    "col_length": "길이",
    "col_url": "URL",
    "col_saved_path": "저장 경로",
    "col_error": "오류",
    "col_depth": "깊이",
    "col_success": "성공",
    "col_category": "범주",
    "col_field": "필드",
    "col_value": "값",
    "col_confidence": "신뢰도",
    "col_location": "위치",
    "col_matched_by": "탐지 방식",
    "col_context": "컨텍스트",
    "log": "실행 로그", "col_ts": "시간", "col_msg": "메시지",
    "clear": "지우기", "save_log": "로그 저장",
    "language": "언어",
    "result_selector": "결과 선택",
    "result_item": "{i}. [{s}] {u}",
    "no_scan": "실행 중인 스캔이 없습니다.",
    "already_running": "이미 스캔이 실행 중입니다.",
    "input_error": "입력 오류",
    "save_title": "저장 파일 선택",
    "no_results": "저장할 결과가 없습니다.",
    "save_log_title": "로그 파일 저장",
    "ssl_warning": "[경고] SSL 인증서 검증 비활성화됨.",
    "stop_requested": "[중지 요청] 현재 요청 완료 후 스캔을 중지합니다.",
    "scan_complete": "{count}개 URL 완료 (성공 {ok}, 실패 {fail})",
    "save_ok": "저장 완료: {path}",
    "save_fail": "저장 실패: {msg}",
    "err_prefix": "[오류] {msg}",
    "workers_label": "작업자: {n}",
    "rate_label": "속도: {r} req/s",
    "queue_label": "대기열: {n}",
    "errors_label": "오류: {n}",
    "elapsed": "{h:02d}:{m:02d}:{s:02d}",
    "req_count": "요청: {n}",
    "dissimilar": "표시 행: {n}",
    "import_hint": "Header-Name: value 형식으로 입력",
    "header_edit_title": "헤더 편집",
    "cell_detail": "셀 상세",
    "copy": "복사", "close": "닫기",
    "empty_title": "아직 표시할 결과가 없습니다",
    "empty_hint": "대상 URL을 입력하고 실행하면 발견된 API, 페이지, JS 파일, 민감정보가 여기에 정리됩니다.",
}

EN: Dict[str, str] = {**KO,
    "app_subtitle": "Precision Workbench",
    "run": "▶  Run", "stop": "■  Stop", "save_results": "⬇  Save Results",
    "exec_status": "Execution Status",
    "idle": "Ready", "running": "Running", "cancelling": "Stopping",
    "saving": "Saving", "done": "Done", "error": "Error",
    "target_url": "Target URLs",
    "url_hint": "Enter one URL per line",
    "url_help": "Add multiple targets on separate lines. Scans run in the order shown.",
    "output_file": "Output File Path",
    "output_hint": "Base filename for results",
    "browse": "Browse",
    "request_headers": "Request Headers",
    "col_name": "Name", "col_value": "Value",
    "add": "Add", "edit": "Edit", "remove": "Remove", "import_": "Import",
    "scan_options": "Scan Options",
    "browser_options": "Browser Analysis",
    "recursive_scan": "Recursive Scan",
    "include_subdomains": "Subdomains",
    "skip_probe": "Skip Probe",
    "verify_ssl": "Verify SSL",
    "max_js": "Max JS",
    "max_depth": "Max Depth",
    "max_workers": "Workers",
    "timeout": "Timeout (s)",
    "request_delay": "Delay (s)",
    "recursive_depth": "Recursive Depth",
    "advanced_options": "Advanced Options",
    "proxy": "Proxy",
    "proxy_hint": "http://127.0.0.1:8080",
    "excluded_sub": "Excluded Subdomains",
    "excluded_hint": "e.g. cdn.example.com",
    "js_dir": "JS Output Folder",
    "filter_hint": "Enter text to filter",
    "quantity": "Quantity", "url_type": "URL Type",
    "status_code": "Status Code",
    "all": "All", "reset": "Reset",
    "col_method": "Method", "col_endpoint": "Endpoint",
    "col_source": "Source", "col_status": "Status Code",
    "col_params": "Parameters", "col_sensitive": "Sensitive",
    "col_severity": "Severity", "col_ctype": "Content Type",
    "col_accessible": "Accessible",
    "col_length": "Length",
    "col_url": "URL",
    "col_saved_path": "Saved Path",
    "col_error": "Error",
    "col_depth": "Depth",
    "col_success": "Success",
    "col_category": "Category",
    "col_field": "Field",
    "col_value": "Value",
    "col_confidence": "Confidence",
    "col_location": "Location",
    "col_matched_by": "Matched By",
    "col_context": "Context",
    "log": "Log", "col_ts": "Timestamp", "col_msg": "Message",
    "clear": "Clear", "save_log": "Save Log",
    "language": "Language",
    "result_selector": "Select Result",
    "no_scan": "No active scan.",
    "already_running": "A scan is already running.",
    "input_error": "Input Error",
    "save_title": "Choose save file",
    "no_results": "No results to save.",
    "save_log_title": "Save log file",
    "ssl_warning": "[Warning] SSL certificate verification disabled.",
    "stop_requested": "[Stop requested] Will stop after current request.",
    "scan_complete": "Scanned {count} URL(s) (success {ok}, failed {fail})",
    "save_ok": "Saved: {path}",
    "save_fail": "Save failed: {msg}",
    "err_prefix": "[Error] {msg}",
    "workers_label": "Workers: {n}",
    "rate_label": "Rate: {r} req/s",
    "queue_label": "Queue: {n}",
    "errors_label": "Errors: {n}",
    "req_count": "Requests: {n}",
    "dissimilar": "Rows: {n}",
    "import_hint": "Enter in Header-Name: value format",
    "header_edit_title": "Edit Header",
    "cell_detail": "Cell Detail",
    "copy": "Copy", "close": "Close",
    "empty_title": "No results to display yet",
    "empty_hint": "Enter target URLs and run a scan to review APIs, pages, JS files, and sensitive findings here.",
}

TEXTS = {"ko": KO, "en": EN}

KO.update({
    "m_sensitive": "민감정보",
    "tab_apis": "APIs",
    "tab_pages": "페이지",
    "tab_js": "JS 파일",
    "tab_sensitive": "민감정보",
    "tab_responses": "전체 결과",
    "filetype_excel_html": "Excel/HTML",
    "filetype_log": "로그 파일",
    "filetype_all": "모든 파일",
    "save_log_error_title": "로그 저장 실패",
})
EN.update({
    "m_sensitive": "Sensitive",
    "tab_apis": "APIs",
    "tab_pages": "Pages",
    "tab_js": "JS Files",
    "tab_sensitive": "Sensitive",
    "tab_responses": "All Results",
    "filetype_excel_html": "Excel/HTML",
    "filetype_log": "Log files",
    "filetype_all": "All files",
    "save_log_error_title": "Save log failed",
})
KO.update({
    "dynamic_analysis": "브라우저로 열어보기",
    "dynamic_actions": "스크롤/클릭 허용 (주의)",
    "dynamic_wait": "화면 로딩 대기(초)",
    "dynamic_events": "저장할 요청 수",
    "dynamic_action_limit": "클릭할 최대 수",
    "dynamic_scroll_steps": "스크롤 횟수",
    "dynamic_recursive_limit": "추가 방문 페이지 수",
    "dynamic_script_body_limit": "JS 분석 크기 제한",
})
EN.update({
    "dynamic_analysis": "Open in Browser",
    "dynamic_actions": "Allow Scrolls/Clicks (Caution)",
    "dynamic_wait": "Wait After Load (s)",
    "dynamic_events": "Requests to Save",
    "dynamic_action_limit": "Max Clicks",
    "dynamic_scroll_steps": "Scroll Count",
    "dynamic_recursive_limit": "Extra Pages to Visit",
    "dynamic_script_body_limit": "JS Analyze Size Limit",
})


def _t(lang: str, key: str, **kw) -> str:
    d = TEXTS.get(lang, KO)
    tpl = d.get(key) or KO.get(key) or key
    return tpl.format(**kw) if kw else tpl


# ── Scan dataclass ────────────────────────────────────────────────────────────

@dataclass
class CtkScanRequest:
    urls: List[str]
    config: Config


# ── Treeview styling ──────────────────────────────────────────────────────────

def _style_treeview() -> None:
    p = _pal()
    s = ttk.Style()
    s.theme_use("default")
    for name, bg, fg, hdr in [
        ("Results.Treeview", p["table_bg"], p["text"], p["table_header_bg"]),
        ("Log.Treeview",     p["table_bg"], p["text"], p["table_header_bg"]),
    ]:
        row_height = 30 if name == "Results.Treeview" else 28
        s.configure(name,
            background=bg, foreground=fg, fieldbackground=bg,
            borderwidth=0, relief="flat", rowheight=row_height,
            font=("Segoe UI", 11),
        )
        s.configure(f"{name}.Heading",
            background=hdr, foreground=p["text"],
            borderwidth=0, relief="flat",
            font=("Segoe UI", 12, "bold"),
            padding=(8, 8),
        )
        s.map(f"{name}.Heading",
            background=[("active", p["border"]), ("pressed", p["border2"])],
            foreground=[("active", p["text"])],
        )
        s.map(name,
            background=[("selected", p["table_selected_bg"])],
            foreground=[("selected", p["table_selected_fg"])],
        )
        s.layout(name, [("Treeview.treearea", {"sticky": "nswe"})])

    # Scrollbar
    s.configure("Vertical.TScrollbar",
        gripcount=0, background=p["border"], troughcolor=p["surface2"],
        borderwidth=0, arrowsize=12,
    )
    s.configure("Horizontal.TScrollbar",
        gripcount=0, background=p["border"], troughcolor=p["surface2"],
        borderwidth=0, arrowsize=12,
    )


# ── Helper widgets ────────────────────────────────────────────────────────────

def _sep(parent: tk.Misc, color: str, height: int = 1) -> tk.Frame:
    return tk.Frame(parent, bg=color, height=height)


class _Badge(tk.Label):
    """Colored rounded-looking label (uses tk.Label with bg/fg)."""
    def __init__(self, parent, text: str, bg: str, fg: str, font=None, **kw):
        fnt = font or ("Segoe UI", 10, "bold")
        super().__init__(parent, text=text, bg=bg, fg=fg, font=fnt,
                         padx=8, pady=3, relief="flat", **kw)


# ── Main window ───────────────────────────────────────────────────────────────

class CtkDiscoveryApp(ctk.CTk):

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(
        self,
        initial_url: Optional[str] = None,
        initial_output: Optional[str] = None,
        initial_js_output_dir: Optional[str] = None,
    ) -> None:
        ctk.set_appearance_mode("Light")
        super().__init__()

        # State
        self._lang: str = "ko"
        self._batch_result: Optional[dict] = None
        self._scan_thread: Optional[threading.Thread] = None
        self._cancel_event: Optional[threading.Event] = None
        self._state: str = "idle"
        self._log_lines: List[str] = []
        self._all_rows: List[dict] = []
        self._headers: Dict[str, str] = {}
        self._start_time: Optional[float] = None
        self._request_count: int = 0
        self._error_count: int = 0
        self._result_records: List[dict] = []
        self._selected_idx: int = -1
        self._timer_id: Optional[str] = None
        self._sort_col: Optional[str] = None
        self._sort_rev: bool = False

        # Tk vars
        self._state_text   = tk.StringVar(value="")
        self._elapsed_text = tk.StringVar(value="00:00:00")
        self._req_text     = tk.StringVar(value=_t(self._lang, "req_count", n=0))
        self._rate_text    = tk.StringVar(value=_t(self._lang, "rate_label", r="0.0"))
        self._result_sel   = tk.StringVar(value="")
        self._filter_var   = tk.StringVar()
        self._qty_var      = tk.StringVar()
        self._type_var     = tk.StringVar()
        self._status_var   = tk.StringVar()
        self._tab_var      = tk.StringVar(value="")
        self._workers_text = tk.StringVar(value=_t(self._lang, "workers_label", n=0))
        self._sb_rate_text = tk.StringVar(value=_t(self._lang, "rate_label", r="0.0"))
        self._queue_text   = tk.StringVar(value=_t(self._lang, "queue_label", n=0))
        self._errors_text  = tk.StringVar(value=_t(self._lang, "errors_label", n=0))

        # Scan option vars
        self._recursive_var   = tk.BooleanVar(value=False)
        self._subdomain_var   = tk.BooleanVar(value=True)
        self._skip_probe_var  = tk.BooleanVar(value=False)
        self._verify_ssl_var  = tk.BooleanVar(value=True)
        self._dynamic_var     = tk.BooleanVar(value=False)
        self._dynamic_actions_var = tk.BooleanVar(value=False)
        self._max_js_var      = tk.IntVar(value=50)
        self._max_depth_var   = tk.IntVar(value=2)
        self._max_workers_var = tk.IntVar(value=8)
        self._timeout_var     = tk.DoubleVar(value=15.0)
        self._delay_var       = tk.DoubleVar(value=0.0)
        self._rec_depth_var   = tk.IntVar(value=1)
        self._dyn_wait_var    = tk.DoubleVar(value=3.0)
        self._dyn_events_var  = tk.IntVar(value=300)
        self._dyn_action_limit_var = tk.IntVar(value=12)
        self._dyn_scroll_steps_var = tk.IntVar(value=3)
        self._dyn_recursive_limit_var = tk.IntVar(value=50)
        self._dyn_script_body_limit_var = tk.IntVar(value=1048576)
        self._proxy_var       = tk.StringVar(value="")
        self._excl_var        = tk.StringVar(value="")
        self._jsdir_var       = tk.StringVar(value=initial_js_output_dir or "")

        # Widget refs (populated during build)
        self._ui: Dict[str, tk.Widget] = {}

        self.title(_t(self._lang, "window_title"))
        self.geometry("1540x920")
        self.minsize(1100, 680)
        self.configure(bg=_pal()["window"])

        _style_treeview()
        self._build_all(initial_url or "", initial_output or "discovery-result")
        self._repaint_ctk_widgets(_pal())
        self._set_state("idle")
        self._refresh_all_texts()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ── Top-level layout ──────────────────────────────────────────────────────

    def _build_all(self, initial_url: str, initial_output: str) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_toolbar(row=0)
        self._build_main(row=1, initial_url=initial_url, initial_output=initial_output)
        self._build_statusbar(row=2)

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self, row: int) -> None:
        p = _pal()
        bar = tk.Frame(self, bg=p["surface"], height=60)
        bar.grid(row=row, column=0, sticky="ew")
        bar.grid_columnconfigure(4, weight=1)
        bar.grid_propagate(False)

        # 1) App identity
        id_f = tk.Frame(bar, bg=p["surface"])
        id_f.grid(row=0, column=0, padx=(16, 0), pady=10, sticky="w")

        icon = tk.Label(id_f, text="⊕", bg=p["accent"], fg="#FFFFFF",
                        font=("Segoe UI", 14, "bold"), padx=6, pady=2)
        icon.pack(side="left", padx=(0, 8))

        title_block = tk.Frame(id_f, bg=p["surface"])
        title_block.pack(side="left")
        tk.Label(title_block, text=_t(self._lang, "app_title"),
                 bg=p["surface"], fg=p["text"],
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        self._ui["subtitle"] = tk.Label(title_block,
                 text=_t(self._lang, "app_subtitle"),
                 bg=p["surface"], fg=p["muted"],
                 font=("Segoe UI", 9))
        self._ui["subtitle"].pack(anchor="w")

        # 2) Divider
        tk.Frame(bar, bg=p["border"], width=1).grid(row=0, column=1, padx=14, pady=8, sticky="ns")

        # 3) Action buttons
        btn_f = tk.Frame(bar, bg=p["surface"])
        btn_f.grid(row=0, column=2, pady=10)

        self._ui["run_btn"] = ctk.CTkButton(
            btn_f, text=_t(self._lang, "run"), width=96, height=34,
            fg_color=p["action_bg"], hover_color=p["action_hover"],
            text_color=p["action_text"], font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6, command=self._on_run,
        )
        self._ui["run_btn"].pack(side="left", padx=(0, 6))

        self._ui["save_btn"] = ctk.CTkButton(
            btn_f, text=_t(self._lang, "save_results"), width=120, height=34,
            fg_color=p["surface2"], hover_color=p["border"],
            text_color=p["text2"], border_width=1, border_color=p["border"],
            corner_radius=6, command=self._on_save,
        )
        self._ui["save_btn"].pack(side="left", padx=(0, 6))

        self._ui["stop_btn"] = ctk.CTkButton(
            btn_f, text=_t(self._lang, "stop"), width=86, height=34,
            fg_color=p["surface2"], hover_color=p["border"],
            text_color=p["text2"], border_width=1, border_color=p["border"],
            corner_radius=6, command=self._on_stop,
        )
        self._ui["stop_btn"].pack(side="left")

        # 4) Divider
        tk.Frame(bar, bg=p["border"], width=1).grid(row=0, column=3, padx=14, pady=8, sticky="nsw")

        # 5) Status strip (stretches)
        status_f = tk.Frame(bar, bg=p["surface"])
        status_f.grid(row=0, column=4, padx=(0, 0), pady=10, sticky="ew")
        bar.grid_columnconfigure(4, weight=1)

        self._ui["exec_lbl"] = tk.Label(status_f, text=_t(self._lang, "exec_status"),
                                        bg=p["surface"], fg=p["text2"],
                                        font=("Segoe UI", 10))
        self._ui["exec_lbl"].pack(side="left", padx=(0, 6))

        self._ui["state_badge"] = tk.Label(status_f, textvariable=self._state_text,
                                           bg=p["badge_idle_fg"], fg="#FFFFFF",
                                           font=("Segoe UI", 10, "bold"),
                                           padx=8, pady=2)
        self._ui["state_badge"].pack(side="left", padx=(0, 8))

        for var, key in [
            (self._elapsed_text, "elapsed_chip"),
            (self._req_text,     "req_chip"),
            (self._rate_text,    "rate_chip"),
        ]:
            lbl = tk.Label(status_f, textvariable=var,
                           bg=p["chip_bg"], fg=p["chip_fg"],
                           font=("Segoe UI", 10, "bold"),
                           padx=7, pady=2)
            lbl.pack(side="left", padx=(0, 4))
            self._ui[key] = lbl

        # 6) Spacer
        tk.Frame(bar, bg=p["surface"]).grid(row=0, column=5, sticky="ew")

        # 7) Right controls
        right_f = tk.Frame(bar, bg=p["surface"])
        right_f.grid(row=0, column=6, padx=(0, 16), pady=10, sticky="e")

        self._ui["lang_lbl"] = tk.Label(right_f, text=_t(self._lang, "language"),
                                        bg=p["surface"], fg=p["text2"],
                                        font=("Segoe UI", 10))
        self._ui["lang_lbl"].pack(side="left", padx=(0, 4))

        self._ui["lang_combo"] = ctk.CTkComboBox(
            right_f, values=["한국어", "English"],
            width=108, height=30,
            fg_color=p["surface2"], border_color=p["border"],
            button_color=p["border"], text_color=p["text"],
            dropdown_fg_color=p["surface"],
            font=ctk.CTkFont(size=11),
            command=self._on_lang_changed, state="readonly",
        )
        self._ui["lang_combo"].set("한국어")
        self._ui["lang_combo"].pack(side="left", padx=(0, 10))

        self._ui["settings_btn"] = ctk.CTkButton(
            right_f, text=_t(self._lang, "settings"), width=92, height=30,
            fg_color=p["surface2"], hover_color=p["border"],
            text_color=p["text2"], border_width=1, border_color=p["border"],
            corner_radius=5, command=lambda: self._ui["output_entry"].focus_set(),
        )
        self._ui["settings_btn"].pack(side="left")

        self._toolbar = bar

    # ── Main body ─────────────────────────────────────────────────────────────

    def _build_main(self, row: int, initial_url: str, initial_output: str) -> None:
        p = _pal()
        body = tk.Frame(self, bg=p["window"])
        body.grid(row=row, column=0, sticky="nsew", padx=12, pady=(8, 0))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self._build_left(body, col=0, initial_url=initial_url, initial_output=initial_output)
        self._build_right(body, col=1)

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left(self, parent: tk.Frame, col: int,
                    initial_url: str, initial_output: str) -> None:
        p = _pal()
        scroll = ctk.CTkScrollableFrame(parent, width=430, fg_color="transparent",
                                         scrollbar_button_color=p["border"],
                                         scrollbar_button_hover_color=p["border2"])
        scroll.grid(row=0, column=col, sticky="nsew", padx=(0, 10))
        scroll.grid_columnconfigure(0, weight=1)

        r = 0

        # Target URLs
        r = self._left_card_urls(scroll, r, initial_url)
        # Output file
        r = self._left_card_output(scroll, r, initial_output)
        # Request headers
        r = self._left_card_headers(scroll, r)
        # Scan options
        r = self._left_card_scan_options(scroll, r)
        # Browser analysis
        r = self._left_card_browser_options(scroll, r)
        # Advanced options
        r = self._left_card_advanced(scroll, r)

    def _section_card(self, parent, row: int, title_key: str) -> Tuple[tk.Frame, int]:
        p = _pal()
        outer = tk.Frame(parent, bg=p["surface"], highlightthickness=1,
                         highlightbackground=p["border"])
        outer.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        outer.grid_columnconfigure(0, weight=1)

        hdr = tk.Frame(outer, bg=p["surface2"])
        hdr.grid(row=0, column=0, sticky="ew")
        _sep(outer, p["border"]).grid(row=1, column=0, sticky="ew")

        lbl = tk.Label(hdr, text=_t(self._lang, title_key),
                       bg=p["surface2"], fg=p["text"],
                       font=("Segoe UI", 11, "bold"), anchor="w",
                       padx=12, pady=7)
        lbl.pack(fill="x")
        self._ui[f"card_{title_key}"] = lbl

        body = tk.Frame(outer, bg=p["surface"])
        body.grid(row=2, column=0, sticky="ew", padx=12, pady=10)
        body.grid_columnconfigure(0, weight=1)
        return body, 0

    def _left_card_urls(self, parent, row: int, initial_url: str) -> int:
        p = _pal()
        body, _ = self._section_card(parent, row, "target_url")
        self._ui["url_help_lbl"] = tk.Label(
            body, text=_t(self._lang, "url_help"),
            bg=p["surface"], fg=p["muted"],
            font=("Segoe UI", 10), anchor="w",
        )
        self._ui["url_help_lbl"].grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._ui["url_box"] = ctk.CTkTextbox(
            body, height=88, font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=p["surface2"], border_color=p["border"], border_width=1,
            text_color=p["text"],
        )
        self._ui["url_box"].grid(row=1, column=0, sticky="ew")
        if initial_url:
            self._ui["url_box"].insert("0.0", initial_url)
        return row + 1

    def _left_card_output(self, parent, row: int, initial_output: str) -> int:
        p = _pal()
        body, _ = self._section_card(parent, row, "output_file")
        row_f = tk.Frame(body, bg=p["surface"])
        row_f.grid(row=0, column=0, sticky="ew")
        row_f.grid_columnconfigure(0, weight=1)
        self._ui["output_entry"] = ctk.CTkEntry(
            row_f, font=ctk.CTkFont(size=12), height=32,
            fg_color=p["surface2"], border_color=p["border"], border_width=1,
            text_color=p["text"],
            placeholder_text=_t(self._lang, "output_hint"),
            placeholder_text_color=p["subtle"],
        )
        self._ui["output_entry"].grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._ui["output_entry"].insert(0, initial_output)
        self._ui["browse_btn"] = ctk.CTkButton(
            row_f, text=_t(self._lang, "browse"), width=80, height=32,
            fg_color=p["surface2"], border_color=p["border"], border_width=1,
            text_color=p["text2"], hover_color=p["border"],
            corner_radius=5, command=self._on_browse,
        )
        self._ui["browse_btn"].grid(row=0, column=1)
        return row + 1

    def _left_card_headers(self, parent, row: int) -> int:
        p = _pal()
        body, _ = self._section_card(parent, row, "request_headers")

        tree_f = tk.Frame(body, bg=p["surface"], highlightthickness=1,
                          highlightbackground=p["border"])
        tree_f.grid(row=0, column=0, sticky="ew")
        tree_f.grid_columnconfigure(0, weight=1)
        self._ui["hdr_tree"] = ttk.Treeview(
            tree_f, columns=("name", "value"), show="headings",
            height=4, style="Results.Treeview",
        )
        self._ui["hdr_tree"].heading("name",  text=_t(self._lang, "col_name"))
        self._ui["hdr_tree"].heading("value", text=_t(self._lang, "col_value"))
        self._ui["hdr_tree"].column("name",  width=130, minwidth=80)
        self._ui["hdr_tree"].column("value", width=180, minwidth=80)
        self._ui["hdr_tree"].grid(row=0, column=0, sticky="ew")

        vsb = ttk.Scrollbar(tree_f, orient="vertical",
                             command=self._ui["hdr_tree"].yview)
        self._ui["hdr_tree"].configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        btn_f = tk.Frame(body, bg=p["surface"])
        btn_f.grid(row=1, column=0, sticky="w", pady=(6, 0))
        for key, cmd in [
            ("add", self._on_hdr_add), ("edit", self._on_hdr_edit),
            ("remove", self._on_hdr_remove), ("import_", self._on_hdr_import),
        ]:
            b = ctk.CTkButton(btn_f, text=_t(self._lang, key), width=58, height=26,
                               fg_color=p["surface2"], border_color=p["border"],
                               border_width=1, text_color=p["text2"],
                               hover_color=p["border"], corner_radius=4,
                               font=ctk.CTkFont(size=11), command=cmd)
            b.pack(side="left", padx=(0, 4))
            self._ui[f"hdr_{key}_btn"] = b
        return row + 1

    def _add_spin_grid(self, parent: tk.Frame, specs: List[Tuple[str, tk.Variable, float, float, bool]], columns: int = 2) -> None:
        p = _pal()
        grid = tk.Frame(parent, bg=p["surface"])
        grid.grid(row=parent.grid_size()[1], column=0, sticky="ew", pady=(2, 0))
        for i, (key, var, mn, mx, fl) in enumerate(specs):
            col = i % columns
            sub_r = i // columns
            sub = tk.Frame(grid, bg=p["surface"])
            sub.grid(row=sub_r, column=col, padx=(0, 12), pady=3, sticky="nw")
            lbl = tk.Label(sub, text=_t(self._lang, key), bg=p["surface"],
                           fg=p["text2"], font=("Segoe UI", 10))
            lbl.pack(anchor="w")
            self._ui[f"lbl_{key}"] = lbl
            spin = tk.Spinbox(sub, textvariable=var, from_=mn, to=mx, increment=0.5 if fl else 1,
                              width=8, font=("Segoe UI", 11),
                              bg=p["surface2"], fg=p["text"],
                              relief="flat", highlightthickness=1,
                              highlightbackground=p["border"],
                              buttonbackground=p["border2"],
                              insertbackground=p["text"],
                              disabledbackground=p["disabled_bg"],
                              disabledforeground=p["disabled_fg"],
                              readonlybackground=p["surface2"])
            spin.pack(anchor="w")
            self._ui[f"spin_{key}"] = spin

    def _left_card_scan_options(self, parent, row: int) -> int:
        p = _pal()
        body, _ = self._section_card(parent, row, "scan_options")

        # Checkboxes row 1
        chk1 = tk.Frame(body, bg=p["surface"])
        chk1.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for key, var in [
            ("recursive_scan", self._recursive_var),
            ("include_subdomains", self._subdomain_var),
        ]:
            cb = ctk.CTkCheckBox(chk1, text=_t(self._lang, key), variable=var,
                                  font=ctk.CTkFont(size=11), text_color=p["text2"],
                                  fg_color=p["accent"], hover_color=p["accent_dark"],
                                  checkmark_color="#FFFFFF", corner_radius=3,
                                  border_color=p["border2"], border_width=1)
            cb.pack(side="left", padx=(0, 14))
            self._ui[f"chk_{key}"] = cb

        # Checkboxes row 2
        chk2 = tk.Frame(body, bg=p["surface"])
        chk2.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for key, var in [
            ("skip_probe",  self._skip_probe_var),
            ("verify_ssl",  self._verify_ssl_var),
        ]:
            cb = ctk.CTkCheckBox(chk2, text=_t(self._lang, key), variable=var,
                                  font=ctk.CTkFont(size=11), text_color=p["text2"],
                                  fg_color=p["accent"], hover_color=p["accent_dark"],
                                  checkmark_color="#FFFFFF", corner_radius=3,
                                  border_color=p["border2"], border_width=1)
            cb.pack(side="left", padx=(0, 14))
            self._ui[f"chk_{key}"] = cb

        self._add_spin_grid(body, [
            ("max_js",       self._max_js_var,      1, 500,  False),
            ("max_depth",    self._max_depth_var,    0,  20,  False),
            ("timeout",      self._timeout_var,    1.0, 300.0, True),
            ("recursive_depth", self._rec_depth_var, 1,  10,  False),
        ], columns=2)

        return row + 1

    def _left_card_browser_options(self, parent, row: int) -> int:
        p = _pal()
        body, _ = self._section_card(parent, row, "browser_options")

        checks = tk.Frame(body, bg=p["surface"])
        checks.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for key, var in [
            ("dynamic_analysis", self._dynamic_var),
            ("dynamic_actions", self._dynamic_actions_var),
        ]:
            cb = ctk.CTkCheckBox(checks, text=_t(self._lang, key), variable=var,
                                  font=ctk.CTkFont(size=11), text_color=p["text2"],
                                  fg_color=p["accent"], hover_color=p["accent_dark"],
                                  checkmark_color="#FFFFFF", corner_radius=3,
                                  border_color=p["border2"], border_width=1)
            cb.pack(side="left", padx=(0, 14))
            self._ui[f"chk_{key}"] = cb

        self._add_spin_grid(body, [
            ("dynamic_wait", self._dyn_wait_var, 0.0, 60.0, True),
            ("dynamic_events", self._dyn_events_var, 1, 5000, False),
            ("dynamic_action_limit", self._dyn_action_limit_var, 0, 100, False),
            ("dynamic_scroll_steps", self._dyn_scroll_steps_var, 0, 20, False),
            ("dynamic_recursive_limit", self._dyn_recursive_limit_var, 0, 1000, False),
            ("dynamic_script_body_limit", self._dyn_script_body_limit_var, 0, 10485760, False),
        ], columns=2)
        return row + 1

    def _left_card_advanced(self, parent, row: int) -> int:
        p = _pal()
        body, _ = self._section_card(parent, row, "advanced_options")
        self._add_spin_grid(body, [
            ("max_workers", self._max_workers_var, 1, 256, False),
            ("request_delay", self._delay_var, 0.0, 60.0, True),
        ], columns=2)

        start_row = body.grid_size()[1]
        for i, (key, var, hint) in enumerate([
            ("proxy",       self._proxy_var,  _t(self._lang, "proxy_hint")),
            ("excluded_sub",self._excl_var,   _t(self._lang, "excluded_hint")),
            ("js_dir",      self._jsdir_var,  ""),
        ]):
            lbl = tk.Label(body, text=_t(self._lang, key), bg=p["surface"],
                           fg=p["text2"], font=("Segoe UI", 10), anchor="w")
            lbl.grid(row=start_row + i * 2, column=0, sticky="w", pady=(8 if i == 0 else 4, 0))
            self._ui[f"lbl_adv_{key}"] = lbl
            ent = ctk.CTkEntry(body, textvariable=var, height=30,
                               font=ctk.CTkFont(size=11),
                               fg_color=p["surface2"], border_color=p["border"],
                               border_width=1, text_color=p["text"],
                               placeholder_text=hint,
                               placeholder_text_color=p["subtle"])
            ent.grid(row=start_row + i * 2 + 1, column=0, sticky="ew", pady=(0, 2))
            self._ui[f"ent_adv_{key}"] = ent
        return row + 1

    # ── Right panel ───────────────────────────────────────────────────────────

    def _build_right(self, parent: tk.Frame, col: int) -> None:
        p = _pal()
        right = tk.Frame(parent, bg=p["window"])
        right.grid(row=0, column=col, sticky="nsew")
        right.grid_rowconfigure(2, weight=4)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_results_header(right, row=0)
        self._build_filter_bar(right, row=1)
        self._build_results_table(right, row=2)
        self._build_log_panel(right, row=3)

    def _build_results_header(self, parent: tk.Frame, row: int) -> None:
        p = _pal()
        hdr = tk.Frame(parent, bg=p["surface"], highlightthickness=1,
                       highlightbackground=p["border"])
        hdr.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        hdr.grid_columnconfigure(1, weight=1)

        # "Results" title + selector
        left_f = tk.Frame(hdr, bg=p["surface"])
        left_f.grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")
        self._ui["results_lbl"] = tk.Label(
            left_f, text=_t(self._lang, "results"),
            bg=p["surface"], fg=p["text"],
            font=("Segoe UI", 16, "bold"),
        )
        self._ui["results_lbl"].pack(side="left")

        sel_f = tk.Frame(hdr, bg=p["surface"])
        sel_f.grid(row=0, column=1, columnspan=2, padx=14, pady=(12, 8), sticky="e")
        self._ui["sel_lbl"] = tk.Label(sel_f, text=_t(self._lang, "result_selector"),
                                       bg=p["surface"], fg=p["text2"],
                                       font=("Segoe UI", 10))
        self._ui["sel_lbl"].pack(side="left", padx=(0, 6))
        self._ui["result_combo"] = ctk.CTkComboBox(
            sel_f, values=["-"], variable=self._result_sel,
            width=240, height=28,
            fg_color=p["surface2"], border_color=p["border"],
            button_color=p["border"], text_color=p["text2"],
            dropdown_fg_color=p["surface"],
            font=ctk.CTkFont(size=11),
            command=self._on_result_selected, state="readonly",
        )
        self._ui["result_combo"].pack(side="left")

        # Metric cards
        cards_f = tk.Frame(hdr, bg=p["surface"])
        cards_f.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

        metric_specs = [
            ("m_summary", "Summary", "_mv_summary"),
            ("m_sensitive",  "Sensitive",  "_mv_sensitive"),
            ("m_js",       "JS Files", "_mv_js"),
            ("m_pages",    "Pages",    "_mv_pages"),
            ("m_apis",     "APIs",     "_mv_apis"),
        ]
        for idx, (key, title, attr) in enumerate(metric_specs):
            cards_f.grid_columnconfigure(idx, weight=1, uniform="metrics")
            color = p[key]
            card = tk.Frame(cards_f, bg=p["surface2"], height=66,
                            highlightthickness=1, highlightbackground=p["border"])
            card.grid(row=0, column=idx, padx=4, sticky="ew")
            card.grid_propagate(False)
            t = tk.Label(card, text=title, bg=p["surface2"], fg=p["text2"],
                         font=("Segoe UI", 10, "bold"))
            t.place(relx=0.5, rely=0.25, anchor="center")
            v = tk.Label(card, text="0", bg=p["surface2"], fg=color,
                         font=("Segoe UI", 20, "bold"))
            v.place(relx=0.5, rely=0.70, anchor="center")
            self._ui[f"mt_{key}"] = t
            setattr(self, attr, v)

    def _tab_values(self) -> List[str]:
        return [
            _t(self._lang, "tab_apis"),
            _t(self._lang, "tab_pages"),
            _t(self._lang, "tab_js"),
            _t(self._lang, "tab_sensitive"),
            _t(self._lang, "tab_responses"),
        ]

    def _build_filter_bar(self, parent: tk.Frame, row: int) -> None:
        p = _pal()
        bar = tk.Frame(parent, bg=p["surface"], highlightthickness=1,
                       highlightbackground=p["border"])
        bar.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        bar.grid_columnconfigure(1, weight=1)

        tab_values = self._tab_values()
        self._tab_var.set(tab_values[0])
        self._ui["tab_selector"] = ctk.CTkSegmentedButton(
            bar, values=tab_values, variable=self._tab_var,
            height=30, selected_color=p["action_bg"],
            selected_hover_color=p["action_hover"],
            unselected_color=p["surface2"],
            unselected_hover_color=p["border"],
            text_color=p["text"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda _: self._apply_filter(),
        )
        self._ui["tab_selector"].grid(row=0, column=0, columnspan=10, sticky="w", padx=10, pady=(8, 0))

        # Search icon
        tk.Label(bar, text="⚲", bg=p["surface"], fg=p["muted"],
                 font=("Segoe UI", 14)).grid(row=1, column=0, padx=(10, 4), pady=8)

        # Filter entry
        self._ui["filter_entry"] = ctk.CTkEntry(
            bar, textvariable=self._filter_var,
            placeholder_text=_t(self._lang, "filter_hint"),
            placeholder_text_color=p["subtle"],
            height=30, font=ctk.CTkFont(size=11),
            fg_color=p["surface2"], border_color=p["border"], border_width=1,
            text_color=p["text"],
        )
        self._ui["filter_entry"].grid(row=1, column=1, sticky="ew", padx=4, pady=8)
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())

        # Dropdowns
        all_lbl = _t(self._lang, "all")
        self._qty_var.set(all_lbl)
        self._type_var.set(all_lbl)
        self._status_var.set(all_lbl)

        for col_idx, (key, var, vals, width) in enumerate([
            ("quantity",    self._qty_var,    [all_lbl, "25", "50", "100", "500"], 120),
            ("url_type",    self._type_var,   [all_lbl, "GET", "POST", "PUT", "DELETE", "HEAD"], 120),
            ("status_code", self._status_var, [all_lbl, "200", "201", "301", "302", "400", "401", "403", "404", "500"], 130),
        ], start=1):
            lbl = tk.Label(bar, text=_t(self._lang, key) + ":",
                           bg=p["surface"], fg=p["text2"],
                           font=("Segoe UI", 10))
            lbl.grid(row=1, column=col_idx * 2, padx=(8, 2), pady=8)
            self._ui[f"filter_lbl_{key}"] = lbl
            combo = ctk.CTkComboBox(
                bar, variable=var, values=vals,
                width=width, height=30,
                fg_color=p["surface2"], border_color=p["border"],
                button_color=p["border"], text_color=p["text2"],
                dropdown_fg_color=p["surface"],
                font=ctk.CTkFont(size=11),
                command=lambda _: self._apply_filter(),
                state="readonly",
            )
            combo.grid(row=1, column=col_idx * 2 + 1, padx=(0, 4), pady=8)
            self._ui[f"filter_combo_{key}"] = combo

        # Dissimilar count label
        self._ui["dissimilar_lbl"] = tk.Label(
            bar, text=_t(self._lang, "dissimilar", n=0),
            bg=p["surface"], fg=p["text2"], font=("Segoe UI", 10),
        )
        self._ui["dissimilar_lbl"].grid(row=1, column=8, padx=(6, 4), pady=8)

        # Reset button
        self._ui["reset_btn"] = ctk.CTkButton(
            bar, text=_t(self._lang, "reset"), width=66, height=30,
            fg_color=p["surface2"], border_color=p["border"], border_width=1,
            text_color=p["text2"], hover_color=p["border"],
            corner_radius=5, command=self._on_reset_filter,
        )
        self._ui["reset_btn"].grid(row=1, column=9, padx=(4, 10), pady=8)

    def _build_results_table(self, parent: tk.Frame, row: int) -> None:
        p = _pal()
        outer = tk.Frame(parent, bg=p["surface"], highlightthickness=1,
                         highlightbackground=p["border"])
        outer.grid(row=row, column=0, sticky="nsew", pady=(0, 6))
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        COLS = ("method","endpoint","status","accessible","length","source","url")
        self._COLS = COLS
        self._active_cols = COLS
        COL_WIDTHS = (82, 280, 90, 80, 80, 220, 360)

        self._ui["tree"] = ttk.Treeview(
            outer, columns=COLS, show="headings",
            style="Results.Treeview", selectmode="browse",
        )
        for col, w in zip(COLS, COL_WIDTHS):
            self._ui["tree"].heading(col,
                text=_t(self._lang, f"col_{col}"),
                command=lambda c=col: self._sort_tree(c),
            )
            self._ui["tree"].column(col, width=w, minwidth=50, anchor="w")

        vsb = ttk.Scrollbar(outer, orient="vertical",   command=self._ui["tree"].yview)
        hsb = ttk.Scrollbar(outer, orient="horizontal", command=self._ui["tree"].xview)
        self._ui["tree"].configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._ui["tree"].grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Row tags for method colors + alt rows
        mp = p
        for method, color_key in [
            ("GET",  "method_get"), ("POST",   "method_post"),
            ("PUT",  "method_put"), ("PATCH",  "method_patch"),
            ("DELETE","method_del"), ("HEAD",  "method_head"),
            ("JS", "m_js"), ("PAGE", "m_pages"),
        ]:
            self._ui["tree"].tag_configure(f"m_{method}", foreground=mp[color_key])
        self._ui["tree"].tag_configure("alt", background=p["table_row_alt"])
        self._ui["tree"].tag_configure("empty", foreground=p["text2"], background=p["field_bg"])
        self._ui["tree"].tag_configure("sensitive_row", foreground=p["m_sensitive"])
        self._ui["tree"].tag_configure("status_error", foreground=p["badge_err_fg"])
        self._ui["tree"].tag_configure("status_warn", foreground=p["method_put"])
        self._ui["tree"].bind("<Double-1>", self._on_tree_dbl)
        self._show_empty_state()

    def _configure_button_role(self, key: str, role: str, p: dict) -> None:
        widget = self._ui.get(key)
        if widget is None:
            return
        styles = {
            "primary": dict(
                fg_color=p["action_bg"], hover_color=p["action_hover"],
                border_color=p["border2"], border_width=1,
                text_color=p["action_text"], text_color_disabled=p["disabled_fg"],
            ),
            "secondary": dict(
                fg_color=p["surface2"], hover_color=p["border2"],
                border_color=p["border"], text_color=p["text2"],
                text_color_disabled=p["disabled_fg"],
            ),
        }
        try:
            widget.configure(**styles[role])
        except Exception:
            pass

    def _configure_input_role(self, key: str, p: dict) -> None:
        widget = self._ui.get(key)
        if widget is None:
            return
        try:
            widget.configure(
                fg_color=p["field_bg"], border_color=p["field_border"],
                text_color=p["text"], placeholder_text_color=p["subtle"],
            )
        except Exception:
            try:
                widget.configure(
                    fg_color=p["field_bg"], border_color=p["field_border"],
                    text_color=p["text"],
                )
            except Exception:
                pass
        try:
            widget.configure(text_color_disabled=p["disabled_fg"])
        except Exception:
            pass

    def _configure_combo_role(self, key: str, p: dict) -> None:
        widget = self._ui.get(key)
        if widget is None:
            return
        try:
            widget.configure(
                fg_color=p["field_bg"], border_color=p["field_border"],
                button_color=p["border"], button_hover_color=p["border2"],
                text_color=p["text2"], dropdown_fg_color=p["surface"],
                dropdown_hover_color=p["surface2"],
                dropdown_text_color=p["text"],
            )
        except Exception:
            pass

    def _configure_dialog(self, dlg: ctk.CTkToplevel, p: dict) -> None:
        try:
            dlg.configure(fg_color=p["surface"])
        except Exception:
            try:
                dlg.configure(bg=p["surface"])
            except Exception:
                pass

    def _dialog_button(self, parent, text: str, command, width: int = 76) -> ctk.CTkButton:
        p = _pal()
        return ctk.CTkButton(
            parent, text=text, width=width,
            fg_color=p["surface2"], hover_color=p["tab_hover"],
            border_color=p["border"], border_width=1,
            text_color=p["text2"], text_color_disabled=p["disabled_fg"],
            command=command,
        )

    def _repaint_ctk_widgets(self, p: dict) -> None:
        for key in ("run_btn",):
            self._configure_button_role(key, "primary", p)
        for key in (
            "save_btn", "stop_btn", "settings_btn", "browse_btn", "reset_btn",
            "hdr_add_btn", "hdr_edit_btn", "hdr_remove_btn", "hdr_import__btn",
            "log_save_log_btn", "log_clear_btn",
        ):
            self._configure_button_role(key, "secondary", p)
        for key in (
            "url_box", "output_entry", "filter_entry",
            "ent_adv_proxy", "ent_adv_excluded_sub", "ent_adv_js_dir",
        ):
            self._configure_input_role(key, p)
        for key in (
            "lang_combo", "result_combo", "filter_combo_quantity",
            "filter_combo_url_type", "filter_combo_status_code",
        ):
            self._configure_combo_role(key, p)
        for key in ("recursive_scan", "include_subdomains", "skip_probe", "verify_ssl", "dynamic_analysis", "dynamic_actions"):
            widget = self._ui.get(f"chk_{key}")
            if widget is not None:
                try:
                    widget.configure(
                        fg_color=p["accent"], hover_color=p["accent_dark"],
                        border_color=p["border2"], text_color=p["text2"],
                        text_color_disabled=p["disabled_fg"],
                    )
                except Exception:
                    pass
        if "tab_selector" in self._ui:
            try:
                self._ui["tab_selector"].configure(
                    selected_color=p["tab_selected_bg"],
                    selected_hover_color=p["action_hover"],
                    unselected_color=p["surface2"],
                    unselected_hover_color=p["tab_hover"],
                    text_color=p["text"],
                    text_color_disabled=p["disabled_fg"],
                )
            except Exception:
                pass
    def _show_empty_state(self) -> None:
        if "tree" not in self._ui:
            return
        tree = self._ui["tree"]
        if tree.get_children():
            return
        title = _t(self._lang, "empty_title")
        hint = _t(self._lang, "empty_hint")
        values = [""] * len(getattr(self, "_active_cols", self._COLS))
        if len(values) >= 2:
            values[1] = title
        if len(values) >= 3:
            values[2] = hint
        tree.insert("", "end", values=tuple(values), tags=("empty",))

    def _is_empty_row(self, item_id: str) -> bool:
        return "empty" in self._ui["tree"].item(item_id, "tags")

    def _build_log_panel(self, parent: tk.Frame, row: int) -> None:
        p = _pal()
        outer = tk.Frame(parent, bg=p["surface"], highlightthickness=1,
                         highlightbackground=p["border"])
        outer.grid(row=row, column=0, sticky="nsew")
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        # Log header bar
        hdr = tk.Frame(outer, bg=p["surface2"])
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        _sep(outer, p["border"]).grid(row=1, column=0, columnspan=2, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        self._ui["log_lbl"] = tk.Label(hdr, text=_t(self._lang, "log"),
                                       bg=p["surface2"], fg=p["text"],
                                       font=("Segoe UI", 11, "bold"), anchor="w",
                                       padx=12, pady=7)
        self._ui["log_lbl"].grid(row=0, column=0, sticky="w")

        btn_f = tk.Frame(hdr, bg=p["surface2"])
        btn_f.grid(row=0, column=1, padx=8, pady=4, sticky="e")
        for key, cmd in [("save_log", self._on_save_log), ("clear", self._on_clear_log)]:
            b = ctk.CTkButton(btn_f, text=_t(self._lang, key), width=80, height=26,
                               fg_color=p["surface2"], border_color=p["border"],
                               border_width=1, text_color=p["text2"],
                               hover_color=p["border"], corner_radius=4,
                               font=ctk.CTkFont(size=10), command=cmd)
            b.pack(side="right", padx=(4, 0))
            self._ui[f"log_{key}_btn"] = b

        # Log treeview
        log_f = tk.Frame(outer, bg=p["surface"])
        log_f.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        log_f.grid_rowconfigure(0, weight=1)
        log_f.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(2, weight=1)

        self._ui["log_tree"] = ttk.Treeview(
            log_f, columns=("ts", "msg"), show="headings",
            style="Log.Treeview", height=6,
        )
        self._ui["log_tree"].heading("ts",  text=_t(self._lang, "col_ts"))
        self._ui["log_tree"].heading("msg", text=_t(self._lang, "col_msg"))
        self._ui["log_tree"].column("ts",  width=155, minwidth=120, stretch=False)
        self._ui["log_tree"].column("msg", width=600, minwidth=200)

        log_vsb = ttk.Scrollbar(log_f, orient="vertical", command=self._ui["log_tree"].yview)
        self._ui["log_tree"].configure(yscrollcommand=log_vsb.set)
        self._ui["log_tree"].grid(row=0, column=0, sticky="nsew")
        log_vsb.grid(row=0, column=1, sticky="ns")
        self._ui["log_tree"].tag_configure("log_error", foreground=p["badge_err_fg"])
        self._ui["log_tree"].tag_configure("log_warn", foreground=p["badge_run_fg"])
        self._ui["log_tree"].tag_configure("log_ok", foreground=p["badge_done_fg"])

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self, row: int) -> None:
        p = _pal()
        bar = tk.Frame(self, bg=p["sb_bg"], height=26)
        bar.grid(row=row, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(4, weight=1)

        for col, var in enumerate([
            self._workers_text, self._sb_rate_text,
            self._queue_text, self._errors_text,
        ]):
            sep = tk.Frame(bar, bg=p["border"], width=1)
            sep.grid(row=0, column=col * 2, padx=0, pady=4, sticky="ns")
            lbl = tk.Label(bar, textvariable=var, bg=p["sb_bg"], fg=p["text2"],
                           font=("Segoe UI", 10), padx=10)
            lbl.grid(row=0, column=col * 2 + 1, sticky="w", pady=4)

        self._sb_bar = bar

    # ── State machine ─────────────────────────────────────────────────────────

    def _set_state(self, state: str) -> None:
        self._state = state
        p = _pal()
        key = state if state in ("idle","running","cancelling","saving","done","error") else "idle"
        self._state_text.set(_t(self._lang, key))

        cfg = {
            "idle":       (p["badge_idle"], p["badge_idle_fg"], True,  False, False),
            "running":    (p["badge_run"],  p["badge_run_fg"],  False, True,  False),
            "cancelling": (p["badge_run"],  p["badge_run_fg"],  False, False, False),
            "saving":     (p["badge_save"], p["badge_save_fg"], False, False, False),
            "done":       (p["badge_done"], p["badge_done_fg"], True,  False, True),
            "error":      (p["badge_err"],  p["badge_err_fg"],  True,  False, False),
        }
        bg, fg, run_en, stop_en, save_en = cfg.get(key, cfg["idle"])

        if "state_badge" in self._ui:
            self._ui["state_badge"].configure(bg=bg, fg=fg)

        run_state  = "normal" if run_en  else "disabled"
        stop_state = "normal" if stop_en else "disabled"
        save_state = "normal" if save_en else "disabled"

        if "run_btn"  in self._ui: self._ui["run_btn"].configure(state=run_state)
        if "stop_btn" in self._ui: self._ui["stop_btn"].configure(state=stop_state)
        if "save_btn" in self._ui: self._ui["save_btn"].configure(state=save_state)
        self._set_scan_inputs_enabled(state not in ("running", "cancelling", "saving"))

        if state not in ("running", "cancelling"):
            self._stop_timer()

    def _set_scan_inputs_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        readonly_state = "readonly" if enabled else "disabled"
        for key in [
            "url_box", "output_entry", "browse_btn",
            "chk_recursive_scan", "chk_include_subdomains",
            "chk_skip_probe", "chk_verify_ssl", "chk_dynamic_analysis", "chk_dynamic_actions",
            "ent_adv_proxy", "ent_adv_excluded_sub", "ent_adv_js_dir",
            "hdr_add_btn", "hdr_edit_btn", "hdr_remove_btn", "hdr_import__btn",
        ]:
            widget = self._ui.get(key)
            if widget is not None:
                try:
                    widget.configure(state=state)
                except Exception:
                    pass
        for key in [
            "spin_max_js", "spin_max_depth", "spin_max_workers",
            "spin_timeout", "spin_request_delay", "spin_recursive_depth",
            "spin_dynamic_wait", "spin_dynamic_events",
            "spin_dynamic_action_limit", "spin_dynamic_scroll_steps",
            "spin_dynamic_recursive_limit", "spin_dynamic_script_body_limit",
        ]:
            widget = self._ui.get(key)
            if widget is not None:
                try:
                    widget.configure(state=state)
                except Exception:
                    pass
        for key in [
            "filter_combo_quantity", "filter_combo_url_type",
            "filter_combo_status_code", "result_combo",
        ]:
            widget = self._ui.get(key)
            if widget is not None:
                try:
                    widget.configure(state=readonly_state)
                except Exception:
                    pass

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _start_timer(self) -> None:
        self._start_time = time.monotonic()
        self._request_count = 0
        self._error_count = 0
        self._tick()

    def _tick(self) -> None:
        if self._state not in ("running", "cancelling"):
            return
        elapsed = time.monotonic() - (self._start_time or time.monotonic())
        rate = self._request_count / elapsed if elapsed > 0 else 0.0
        self._update_runtime_labels(elapsed=elapsed, rate=rate)
        self._timer_id = self.after(500, self._tick)

    def _update_runtime_labels(self, elapsed: Optional[float] = None, rate: Optional[float] = None) -> None:
        elapsed = 0.0 if elapsed is None else max(0.0, elapsed)
        h, rem = divmod(int(elapsed), 3600)
        m, s = divmod(rem, 60)
        display_rate = 0.0 if rate is None else rate
        workers = getattr(self._current_config, "max_workers", 0) if hasattr(self, "_current_config") else 0
        self._elapsed_text.set(_t(self._lang, "elapsed", h=h, m=m, s=s))
        self._req_text.set(_t(self._lang, "req_count", n=f"{self._request_count:,}"))
        self._rate_text.set(_t(self._lang, "rate_label", r=f"{display_rate:.1f}"))
        self._workers_text.set(_t(self._lang, "workers_label", n=workers))
        self._sb_rate_text.set(_t(self._lang, "rate_label", r=f"{display_rate:.1f}"))
        self._queue_text.set(_t(self._lang, "queue_label", n=0))
        self._errors_text.set(_t(self._lang, "errors_label", n=self._error_count))

    def _stop_timer(self) -> None:
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _on_run(self) -> None:
        if self._state == "running":
            messagebox.showwarning("", _t(self._lang, "already_running"), parent=self)
            return

        output_str = self._ui["output_entry"].get().strip() or "discovery-result"
        try:
            url_text = self._ui["url_box"].get("0.0", "end").strip()
            urls = parse_input_urls(url_text)
            excluded = parse_hostname_filters(
                [s.strip() for s in self._excl_var.get().split(",") if s.strip()]
            )
            cfg = Config(
                url=urls[0],
                max_js_files=self._max_js_var.get(),
                max_depth=self._max_depth_var.get(),
                timeout=float(self._timeout_var.get()),
                output=Path(output_str),
                skip_probe=self._skip_probe_var.get(),
                recursive_scan=self._recursive_var.get(),
                recursive_depth=self._rec_depth_var.get(),
                include_subdomains=self._subdomain_var.get(),
                excluded_subdomains=excluded,
                max_workers=self._max_workers_var.get(),
                request_delay=float(self._delay_var.get()),
                headers=dict(self._headers),
                verify_ssl=self._verify_ssl_var.get(),
                proxy_url=self._proxy_var.get().strip(),
                js_output_dir=Path(self._jsdir_var.get()) if self._jsdir_var.get().strip() else None,
                dynamic_analysis=self._dynamic_var.get(),
                dynamic_wait=float(self._dyn_wait_var.get()),
                dynamic_max_events=self._dyn_events_var.get(),
                dynamic_action_scan=self._dynamic_actions_var.get(),
                dynamic_action_limit=self._dyn_action_limit_var.get(),
                dynamic_scroll_steps=self._dyn_scroll_steps_var.get(),
                dynamic_recursive_limit=self._dyn_recursive_limit_var.get(),
                dynamic_script_body_limit=self._dyn_script_body_limit_var.get(),
            )
            validate_config(cfg)
        except Exception as exc:
            messagebox.showerror(_t(self._lang, "input_error"), str(exc), parent=self)
            return

        self._current_config = cfg
        if not cfg.verify_ssl:
            self._log(_t(self._lang, "ssl_warning"))

        self._batch_result = None
        self._result_records = []
        self._all_rows = []
        self._clear_table()
        self._reset_metrics()
        self._set_state("running")
        self._start_timer()

        cancel_event = threading.Event()
        self._cancel_event = cancel_event
        req = CtkScanRequest(urls=urls, config=cfg)
        self._scan_thread = threading.Thread(
            target=self._worker, args=(req, cancel_event), daemon=True)
        self._scan_thread.start()

    def _bump_request_count(self) -> None:
        self._request_count += 1

    def _bump_error_count(self) -> None:
        self._error_count += 1

    def _worker(self, req: CtkScanRequest, cancel_event: threading.Event) -> None:
        try:
            execution = build_execution_context(req.config)
            execution.cancel_event = cancel_event

            def on_progress(msg: str) -> None:
                self.after(0, self._bump_request_count)
                self.after(0, lambda m=msg: self._log(m))

            result = discover_many(req.config, req.urls,
                                   progress=on_progress, execution=execution)
            if cancel_event.is_set():
                raise ScanCancelled(CANCEL_MESSAGE)
            self.after(0, lambda r=result: self._on_finished(r))
        except ScanCancelled:
            self.after(0, self._on_cancelled)
        except Exception as exc:
            self.after(0, self._bump_error_count)
            self.after(0, lambda m=str(exc): self._on_error(m))

    def _on_finished(self, batch: dict) -> None:
        self._batch_result = batch
        records = batch.get("results") or []
        self._result_records = records
        s = batch.get("summary") or {}
        msg = _t(self._lang, "scan_complete",
                 count=len(records), ok=s.get("success_count", 0),
                 fail=s.get("failed_count", 0))
        self._log(msg)
        self._update_metrics(batch)
        self._populate_selector(records)
        if records:
            self._select_result(0)
        self._set_state("done")

    def _on_cancelled(self) -> None:
        self._log(_t(self._lang, "stop_requested"))
        self._set_state("idle")

    def _on_error(self, msg: str) -> None:
        self._log(_t(self._lang, "err_prefix", msg=msg))
        self._set_state("error")

    def _on_stop(self) -> None:
        if not self._cancel_event or self._state != "running":
            messagebox.showinfo("", _t(self._lang, "no_scan"), parent=self)
            return
        self._cancel_event.set()
        self._log(_t(self._lang, "stop_requested"))
        self._set_state("cancelling")

    def _on_save(self) -> None:
        if not self._batch_result:
            messagebox.showinfo("", _t(self._lang, "no_results"), parent=self)
            return
        path = filedialog.asksaveasfilename(
            title=_t(self._lang, "save_title"),
            defaultextension=".xlsx",
            filetypes=[
                (_t(self._lang, "filetype_excel_html"), "*.xlsx *.html"),
                (_t(self._lang, "filetype_all"), "*"),
            ],
            parent=self,
        )
        if not path:
            return
        self._set_state("saving")
        def do_save():
            try:
                saved = save_export_bundle(Path(path), self._batch_result)
                self.after(0, lambda p=saved: self._on_save_ok(p))
            except Exception as exc:
                self.after(0, lambda m=str(exc): self._on_save_fail(m))
        threading.Thread(target=do_save, daemon=True).start()

    def _on_save_ok(self, paths) -> None:
        label = str(paths[0]) if paths else ""
        self._log(_t(self._lang, "save_ok", path=label))
        self._set_state("done")

    def _on_save_fail(self, msg: str) -> None:
        self._log(_t(self._lang, "save_fail", msg=msg))
        self._set_state("error")

    # ── Results table ─────────────────────────────────────────────────────────

    def _populate_selector(self, records: List[dict]) -> None:
        items = ["-"] if not records else [
            _t(self._lang, "result_item",
               i=i + 1,
               s=(r.get("status") or "?")[:1].upper(),
               u=(r.get("target_url") or r.get("url") or "")[:55])
            for i, r in enumerate(records)
        ]
        self._ui["result_combo"].configure(values=items)
        self._ui["result_combo"].set(items[0])

    def _on_result_selected(self, choice: str) -> None:
        items = self._ui["result_combo"].cget("values")
        if choice in items:
            self._select_result(items.index(choice))

    def _select_result(self, idx: int) -> None:
        if not (0 <= idx < len(self._result_records)):
            return
        self._selected_idx = idx
        rec = self._result_records[idx]
        self._all_rows = self._build_rows(rec)
        self._apply_filter()
        self._update_metrics_from_record(rec)

    def _api_items(self, record: dict) -> List[dict]:
        items: List[dict] = []
        seen: set[str] = set()
        for key, accessible_default in (
            ("all_apis", None),
            ("accessible_apis", True),
            ("probe_results", None),
        ):
            for item in record.get(key) or []:
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

    def _source_text(self, item: dict) -> str:
        sources = item.get("sources")
        if isinstance(sources, (list, tuple, set)):
            return ", ".join(str(source) for source in sources)
        if sources:
            return str(sources)
        return str(item.get("source") or "")

    def _page_items(self, record: dict) -> List[dict]:
        items: List[dict] = []
        seen: set[str] = set()
        for key, accessible_default in (
            ("all_pages", None),
            ("accessible_pages", True),
        ):
            for item in record.get(key) or []:
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

    def _build_rows(self, record: dict) -> List[dict]:
        rows: List[dict] = []
        for item in self._api_items(record):
            rows.append({
                "kind":      "api",
                "method":    str(item.get("method") or item.get("probe_method") or ""),
                "endpoint":  str(item.get("path") or item.get("endpoint") or item.get("url") or ""),
                "source":    self._source_text(item),
                "status":    str(item.get("status_code") or item.get("status") or "-"),
                "params":    str(item.get("parameters") or item.get("length") or ""),
                "accessible": "Y" if item.get("accessible") is True else ("N" if item.get("accessible") is False else "-"),
                "length":    str(item.get("length") or ""),
                "url":       str(item.get("url") or ""),
                "error":     str(item.get("probe_error") or item.get("error") or ""),
                "sensitive": "",
                "severity":  "",
                "ctype":     str(item.get("content_type") or ""),
            })
        for item in self._page_items(record):
            rows.append({
                "kind":      "page",
                "method":    "PAGE",
                "endpoint":  str(item.get("path") or item.get("url") or ""),
                "source":    self._source_text(item),
                "status":    str(item.get("status_code") or "-"),
                "params":    str(item.get("length") or ""),
                "accessible": "Y" if item.get("accessible") is True else ("N" if item.get("accessible") is False else "-"),
                "length":    str(item.get("length") or ""),
                "url":       str(item.get("url") or ""),
                "error":     str(item.get("probe_error") or item.get("error") or ""),
                "sensitive": "",
                "severity":  "",
                "ctype":     "text/html",
            })
        for item in record.get("js_files") or []:
            rows.append({
                "kind":      "js",
                "method":    "JS",
                "endpoint":  str(item.get("url") or ""),
                "source":    str(item.get("saved_path") or ""),
                "status":    str(item.get("status_code") or "-"),
                "params":    str(item.get("length") or ""),
                "depth":     str(item.get("depth") or "0"),
                "success":   "Y" if item.get("success") else "N",
                "length":    str(item.get("length") or ""),
                "url":       str(item.get("url") or ""),
                "saved_path": str(item.get("saved_path") or ""),
                "error":     str(item.get("error") or item.get("save_error") or ""),
                "sensitive": "",
                "severity":  "",
                "ctype":     "application/javascript",
            })
        for f in resolve_sensitive_findings(record):
            line = str(f.get("line") or "")
            column = str(f.get("column") or "")
            location = f"{line}:{column}" if line or column else str(f.get("location") or "")
            rows.append({
                "kind":      "sensitive",
                "method":    "",
                "endpoint":  location,
                "source":    str(f.get("source_label") or f.get("source") or f.get("source_url") or ""),
                "status":    "",
                "params":    "",
                "sensitive": str(f.get("type") or f.get("category") or ""),
                "severity":  str(f.get("severity") or ""),
                "ctype":     str(f.get("value") or f.get("masked_value") or ""),
                "category":  str(f.get("category") or f.get("type") or ""),
                "field":     str(f.get("field_name") or ""),
                "value":     str(f.get("value") or f.get("masked_value") or ""),
                "confidence": str(f.get("confidence") or ""),
                "location":  location,
                "matched_by": str(f.get("matched_by") or ""),
                "context":   str(f.get("context") or ""),
                "url":       str(f.get("source_url") or ""),
            })
        return rows

    def _columns_for_current_tab(self) -> Tuple[Tuple[str, int], ...]:
        selected_tab = self._tab_var.get()
        if selected_tab == _t(self._lang, "tab_apis"):
            return (("method", 82), ("status", 90), ("accessible", 80), ("length", 80), ("source", 240), ("url", 460))
        if selected_tab == _t(self._lang, "tab_pages"):
            return (("status", 90), ("accessible", 80), ("length", 80), ("source", 260), ("url", 480), ("error", 240))
        if selected_tab == _t(self._lang, "tab_js"):
            return (("depth", 70), ("status", 90), ("success", 80), ("length", 90), ("saved_path", 240), ("error", 220), ("url", 440))
        if selected_tab == _t(self._lang, "tab_sensitive"):
            return (("severity", 90), ("confidence", 90), ("category", 120), ("field", 150), ("value", 180), ("location", 90), ("source", 220), ("matched_by", 180), ("context", 360))
        return (("kind", 90), ("method", 82), ("endpoint", 260), ("status", 90), ("source", 220), ("severity", 90), ("sensitive", 120), ("url", 360))

    def _configure_result_columns(self) -> None:
        tree = self._ui["tree"]
        specs = self._columns_for_current_tab()
        cols = tuple(key for key, _ in specs)
        if getattr(self, "_active_cols", ()) != cols:
            self._active_cols = cols
            tree.configure(columns=cols)
        for key, width in specs:
            tree.heading(key, text=_t(self._lang, f"col_{key}"), command=lambda c=key: self._sort_tree(c))
            tree.column(key, width=width, minwidth=50, anchor="w")

    def _row_value(self, row: dict, column: str) -> str:
        if column == "kind":
            return str(row.get("kind") or "")
        return str(row.get(column, "") or "")

    def _refresh_table(self, rows: List[dict]) -> None:
        tree = self._ui["tree"]
        self._configure_result_columns()
        self._clear_table()
        for i, r in enumerate(rows):
            method = r["method"].upper()
            tags = [f"m_{method}"] if method in ("GET","POST","PUT","PATCH","DELETE","HEAD") else []
            if method in ("JS", "PAGE"):
                tags.append(f"m_{method}")
            if r.get("kind") == "sensitive":
                tags.append("sensitive_row")
            status_parts = str(r.get("status") or "").split()
            try:
                status_num = int(status_parts[0]) if status_parts else 0
            except ValueError:
                status_num = 0
            if status_num >= 500:
                tags.append("status_error")
            elif status_num >= 400:
                tags.append("status_warn")
            if i % 2:
                tags.append("alt")
            tree.insert("", "end",
                values=tuple(self._row_value(r, column) for column in self._active_cols),
                tags=tags,
            )
        if not rows:
            self._show_empty_state()
        # Update dissimilar count
        if "dissimilar_lbl" in self._ui:
            self._ui["dissimilar_lbl"].configure(
                text=_t(self._lang, "dissimilar", n=len(rows)))

    def _clear_table(self) -> None:
        for ch in self._ui["tree"].get_children():
            self._ui["tree"].delete(ch)

    def _apply_filter(self) -> None:
        q = self._filter_var.get().lower()
        quantity_f = self._qty_var.get()
        method_f = self._type_var.get()
        status_f = self._status_var.get()
        all_v = _t(self._lang, "all")
        selected_tab = self._tab_var.get()
        tab_kind = {
            _t(self._lang, "tab_apis"): "api",
            _t(self._lang, "tab_pages"): "page",
            _t(self._lang, "tab_js"): "js",
            _t(self._lang, "tab_sensitive"): "sensitive",
        }.get(selected_tab)
        rows = [
            r for r in self._all_rows
            if (not q or q in " ".join(str(value) for value in r.values()).lower())
            and (tab_kind is None or r.get("kind") == tab_kind)
            and (method_f == all_v or r["method"].upper() == method_f)
            and (status_f == all_v or r["status"] == status_f)
        ]
        if quantity_f != all_v:
            try:
                rows = rows[:int(quantity_f)]
            except ValueError:
                pass
        self._refresh_table(rows)

    def _on_reset_filter(self) -> None:
        self._filter_var.set("")
        all_v = _t(self._lang, "all")
        self._qty_var.set(all_v)
        self._type_var.set(all_v)
        self._status_var.set(all_v)
        if "filter_combo_quantity" in self._ui:
            self._ui["filter_combo_quantity"].set(all_v)
        if "filter_combo_url_type" in self._ui:
            self._ui["filter_combo_url_type"].set(all_v)
        if "filter_combo_status_code" in self._ui:
            self._ui["filter_combo_status_code"].set(all_v)
        self._apply_filter()

    def _sort_tree(self, col: str) -> None:
        tree = self._ui["tree"]
        items = [(tree.item(k, "values"), k) for k in tree.get_children("")]
        col_idx = list(getattr(self, "_active_cols", self._COLS)).index(col)
        rev = self._sort_rev if self._sort_col == col else False
        def sort_key(x):
            v = x[0][col_idx]
            try: return (0, int(v))
            except (ValueError, IndexError): return (1, v.lower())
        items.sort(key=sort_key, reverse=rev)
        for i, (_, k) in enumerate(items):
            tree.move(k, "", i)
            cur_tags = list(tree.item(k, "tags"))
            cur_tags = [t for t in cur_tags if t != "alt"]
            if i % 2: cur_tags.append("alt")
            tree.item(k, tags=cur_tags)
        self._sort_col = col
        self._sort_rev = not rev if self._sort_col == col else False

    def _on_tree_dbl(self, event) -> None:
        if self._ui["tree"].identify("region", event.x, event.y) != "cell":
            return
        col_id = self._ui["tree"].identify_column(event.x)
        row_id = self._ui["tree"].identify_row(event.y)
        if not row_id:
            return
        if self._is_empty_row(row_id):
            return
        col_idx = int(col_id.replace("#", "")) - 1
        vals = self._ui["tree"].item(row_id, "values")
        if col_idx < len(vals):
            self._cell_detail(str(vals[col_idx]))

    def _cell_detail(self, text: str) -> None:
        p = _pal()
        dlg = ctk.CTkToplevel(self)
        dlg.title(_t(self._lang, "cell_detail"))
        dlg.geometry("620x300")
        self._configure_dialog(dlg, p)
        dlg.grab_set()
        tb = ctk.CTkTextbox(dlg, font=ctk.CTkFont(family="Segoe UI", size=12),
                             fg_color=p["field_bg"], border_color=p["field_border"],
                             border_width=1, text_color=p["text"])
        tb.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        tb.insert("0.0", text)
        bf = tk.Frame(dlg, bg=p["surface"])
        bf.pack(fill="x", padx=12, pady=(0, 12))
        self._dialog_button(
            bf, _t(self._lang, "copy"),
            lambda: (self.clipboard_clear(), self.clipboard_append(text)),
        ).pack(side="right", padx=(6, 0))
        self._dialog_button(bf, _t(self._lang, "close"), dlg.destroy).pack(side="right")

    # ── Metrics ───────────────────────────────────────────────────────────────

    def _reset_metrics(self) -> None:
        for attr in ("_mv_summary","_mv_sensitive","_mv_js","_mv_pages","_mv_apis"):
            getattr(self, attr).configure(text="0")

    def _summary_count(self, summary: dict, key: str, fallback: int) -> int:
        try:
            value = int(summary.get(key, 0) or 0)
        except (TypeError, ValueError):
            value = 0
        return value or fallback

    def _update_metrics(self, batch: dict) -> None:
        s = batch.get("summary") or {}
        records = batch.get("results") or []
        self._mv_summary.configure(text=f"{len(records):,}")
        sensitive_total = s.get("sensitive_total", s.get("hardcoded_total", 0))
        js_total = self._summary_count(s, "js_fetched", sum(len(r.get("js_files") or []) for r in records))
        page_total = self._summary_count(s, "page_count", sum(len(self._page_items(r)) for r in records))
        api_total = self._summary_count(s, "api_count", sum(len(self._api_items(r)) for r in records))
        self._mv_sensitive.configure(text=f"{sensitive_total:,}")
        self._mv_js.configure(text=f"{js_total:,}")
        self._mv_pages.configure(text=f"{page_total:,}")
        self._mv_apis.configure(text=f"{api_total:,}")

    def _update_metrics_from_record(self, rec: dict) -> None:
        s = rec.get("summary") or {}
        js_total = self._summary_count(s, "js_fetched", len(rec.get("js_files") or []))
        page_total = self._summary_count(s, "page_count", len(self._page_items(rec)))
        api_total = self._summary_count(s, "api_count", len(self._api_items(rec)))
        self._mv_summary.configure(text=f"{len(self._all_rows):,}")
        self._mv_sensitive.configure(text=f"{len(resolve_sensitive_findings(rec)):,}")
        self._mv_js.configure(text=f"{js_total:,}")
        self._mv_pages.configure(text=f"{page_total:,}")
        self._mv_apis.configure(text=f"{api_total:,}")

    # ── Log ───────────────────────────────────────────────────────────────────

    def _log(self, message: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self._log_lines.append(f"{ts}\t{message}")
        tree = self._ui["log_tree"]
        lower = message.lower()
        tags = []
        if "오류" in message or "error" in lower or "failed" in lower or "실패" in message:
            tags.append("log_error")
        elif "경고" in message or "warning" in lower or "중지" in message or "stop" in lower:
            tags.append("log_warn")
        elif "완료" in message or "saved" in lower or "저장 완료" in message:
            tags.append("log_ok")
        tree.insert("", "end", values=(ts, message), tags=tags)
        children = tree.get_children()
        if children:
            tree.see(children[-1])

    def _on_clear_log(self) -> None:
        self._log_lines.clear()
        for ch in self._ui["log_tree"].get_children():
            self._ui["log_tree"].delete(ch)

    def _on_save_log(self) -> None:
        path = filedialog.asksaveasfilename(
            title=_t(self._lang, "save_log_title"),
            defaultextension=".log",
            filetypes=[
                (_t(self._lang, "filetype_log"), "*.log *.txt"),
                (_t(self._lang, "filetype_all"), "*"),
            ],
            parent=self,
        )
        if path:
            try:
                Path(path).write_text("\n".join(self._log_lines), encoding="utf-8")
            except Exception as exc:
                messagebox.showerror(
                    _t(self._lang, "save_log_error_title"),
                    _t(self._lang, "err_prefix", msg=str(exc)),
                    parent=self,
                )

    # ── Headers ───────────────────────────────────────────────────────────────

    def _on_hdr_add(self)    -> None: self._hdr_dialog(None)
    def _on_hdr_edit(self)   -> None:
        sel = self._ui["hdr_tree"].selection()
        if sel:
            self._hdr_dialog(self._ui["hdr_tree"].item(sel[0], "values")[0])

    def _on_hdr_remove(self) -> None:
        sel = self._ui["hdr_tree"].selection()
        if sel:
            name = self._ui["hdr_tree"].item(sel[0], "values")[0]
            self._headers.pop(name, None)
            self._ui["hdr_tree"].delete(sel[0])

    def _upsert_header(self, name: str, value: str) -> None:
        self._headers[name] = value
        for iid in self._ui["hdr_tree"].get_children():
            if self._ui["hdr_tree"].item(iid, "values")[0] == name:
                self._ui["hdr_tree"].item(iid, values=(name, value))
                return
        self._ui["hdr_tree"].insert("", "end", values=(name, value))

    def _on_hdr_import(self) -> None:
        p = _pal()
        dlg = ctk.CTkToplevel(self)
        dlg.title(_t(self._lang, "import_"))
        dlg.geometry("380x220")
        self._configure_dialog(dlg, p)
        dlg.grab_set()
        tk.Label(dlg, text=_t(self._lang, "import_hint"),
                 bg=p["surface"], fg=p["text2"],
                 font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(10, 4))
        tb = ctk.CTkTextbox(dlg, font=ctk.CTkFont(size=11),
                             fg_color=p["field_bg"], border_color=p["field_border"],
                             border_width=1, text_color=p["text"])
        tb.pack(fill="both", expand=True, padx=12, pady=4)
        def apply():
            try:
                headers = parse_header_lines(tb.get("0.0", "end"))
            except ValueError as exc:
                messagebox.showerror(_t(self._lang, "input_error"), str(exc), parent=dlg)
                return
            for k, v in headers.items():
                self._upsert_header(k, v)
            dlg.destroy()
        self._dialog_button(dlg, "OK", apply).pack(pady=(4, 10))

    def _hdr_dialog(self, edit_name: Optional[str]) -> None:
        p = _pal()
        dlg = ctk.CTkToplevel(self)
        dlg.title(_t(self._lang, "header_edit_title"))
        dlg.geometry("340x170")
        self._configure_dialog(dlg, p)
        dlg.grab_set()
        nv = tk.StringVar(value=edit_name or "")
        vv = tk.StringVar(value=self._headers.get(edit_name or "", ""))
        for key_label, var in [(_t(self._lang, "col_name"), nv),
                                (_t(self._lang, "col_value"), vv)]:
            tk.Label(dlg, text=key_label, bg=p["surface"], fg=p["text2"],
                     font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkEntry(dlg, textvariable=var, font=ctk.CTkFont(size=12),
                         fg_color=p["field_bg"], border_color=p["field_border"],
                         text_color=p["text"]
                         ).pack(fill="x", padx=12)
        def apply():
            try:
                n, v = parse_header_entry(nv.get(), vv.get())
            except ValueError as exc:
                messagebox.showerror(_t(self._lang, "input_error"), str(exc), parent=dlg)
                return
            if edit_name and edit_name != n:
                self._headers.pop(edit_name, None)
                for iid in self._ui["hdr_tree"].get_children():
                    if self._ui["hdr_tree"].item(iid, "values")[0] == edit_name:
                        self._ui["hdr_tree"].delete(iid); break
            self._upsert_header(n, v)
            dlg.destroy()
        self._dialog_button(dlg, "OK", apply).pack(pady=(10, 12))

    def _on_browse(self) -> None:
        p = filedialog.asksaveasfilename(
            title=_t(self._lang, "save_title"),
            defaultextension=".xlsx",
            filetypes=[("Excel/HTML", "*.xlsx *.html"), ("All files", "*")],
            parent=self,
        )
        if p:
            self._ui["output_entry"].delete(0, "end")
            self._ui["output_entry"].insert(0, p)

    # ── Language ──────────────────────────────────────────────────────────────

    def _on_lang_changed(self, choice: str) -> None:
        tab_keys = {
            _t(self._lang, "tab_apis"): "tab_apis",
            _t(self._lang, "tab_pages"): "tab_pages",
            _t(self._lang, "tab_js"): "tab_js",
            _t(self._lang, "tab_sensitive"): "tab_sensitive",
            _t(self._lang, "tab_responses"): "tab_responses",
        }
        selected_tab_key = tab_keys.get(self._tab_var.get(), "tab_apis")
        all_values = {"전체", "All"}
        filter_was_all = {
            "quantity": self._qty_var.get() in all_values,
            "url_type": self._type_var.get() in all_values,
            "status_code": self._status_var.get() in all_values,
        }
        self._lang = "en" if choice == "English" else "ko"
        self._refresh_all_texts()
        selected_tab = _t(self._lang, selected_tab_key)
        self._tab_var.set(selected_tab)
        if "tab_selector" in self._ui:
            try:
                self._ui["tab_selector"].set(selected_tab)
            except Exception:
                pass
        all_label = _t(self._lang, "all")
        for key, var in [
            ("quantity", self._qty_var),
            ("url_type", self._type_var),
            ("status_code", self._status_var),
        ]:
            if filter_was_all[key]:
                var.set(all_label)
                combo = self._ui.get(f"filter_combo_{key}")
                if combo is not None:
                    try:
                        combo.set(all_label)
                    except Exception:
                        pass
        self._apply_filter()

    def _repaint_tree_widgets(self, p: dict) -> None:
        """Refresh ttk Treeview styles and per-row tags for the active theme."""
        _style_treeview()
        if "tree" in self._ui:
            for method, ck in [
                ("GET", "method_get"), ("POST", "method_post"),
                ("PUT", "method_put"), ("PATCH", "method_patch"),
                ("DELETE", "method_del"), ("HEAD", "method_head"),
                ("JS", "m_js"), ("PAGE", "m_pages"),
            ]:
                self._ui["tree"].tag_configure(f"m_{method}", foreground=p[ck])
            self._ui["tree"].tag_configure("alt", background=p["table_row_alt"])
            self._ui["tree"].tag_configure("empty", foreground=p["text2"], background=p["field_bg"])
            self._ui["tree"].tag_configure("sensitive_row", foreground=p["m_sensitive"])
            self._ui["tree"].tag_configure("status_error", foreground=p["badge_err_fg"])
            self._ui["tree"].tag_configure("status_warn", foreground=p["method_put"])
        if "log_tree" in self._ui:
            self._ui["log_tree"].tag_configure("log_error", foreground=p["badge_err_fg"])
            self._ui["log_tree"].tag_configure("log_warn", foreground=p["badge_run_fg"])
            self._ui["log_tree"].tag_configure("log_ok", foreground=p["badge_done_fg"])

    def _refresh_all_texts(self) -> None:
        self.title(_t(self._lang, "window_title"))
        # widget text map
        mapping = {
            "subtitle":        "app_subtitle",
            "exec_lbl":        "exec_status",
            "url_help_lbl":     "url_help",
            "results_lbl":     "results",
            "sel_lbl":         "result_selector",
            "log_lbl":         "log",
        }
        for wkey, tkey in mapping.items():
            if wkey in self._ui:
                w = self._ui[wkey]
                if hasattr(w, "configure"):
                    w.configure(text=_t(self._lang, tkey))

        # Buttons
        btn_map = {
            "run_btn":         "run",
            "stop_btn":        "stop",
            "save_btn":        "save_results",
            "browse_btn":      "browse",
            "settings_btn":    "settings",
            "reset_btn":       "reset",
            "log_save_log_btn":"save_log",
            "log_clear_btn":   "clear",
            "hdr_add_btn":     "add",
            "hdr_edit_btn":    "edit",
            "hdr_remove_btn":  "remove",
            "hdr_import__btn": "import_",
        }
        for wkey, tkey in btn_map.items():
            if wkey in self._ui:
                try: self._ui[wkey].configure(text=_t(self._lang, tkey))
                except Exception: pass

        # Card titles
        for key in ("target_url","output_file","request_headers",
                    "scan_options","browser_options","advanced_options"):
            wkey = f"card_{key}"
            if wkey in self._ui:
                self._ui[wkey].configure(text=_t(self._lang, key))

        # Metric card titles
        for key in ("m_summary","m_sensitive","m_js","m_pages","m_apis"):
            wkey = f"mt_{key}"
            if wkey in self._ui:
                title = _t(self._lang, key)
                self._ui[wkey].configure(text=title)

        if "tab_selector" in self._ui:
            tab_values = self._tab_values()
            self._ui["tab_selector"].configure(values=tab_values)
            if self._tab_var.get() not in tab_values:
                self._tab_var.set(tab_values[0])

        all_lbl = _t(self._lang, "all")
        filter_values = {
            "quantity": [all_lbl, "25", "50", "100", "500"],
            "url_type": [all_lbl, "GET", "POST", "PUT", "DELETE", "HEAD"],
            "status_code": [all_lbl, "200", "201", "301", "302", "400", "401", "403", "404", "500"],
        }
        for key, values in filter_values.items():
            combo = self._ui.get(f"filter_combo_{key}")
            if combo is not None:
                try:
                    combo.configure(values=values)
                except Exception:
                    pass

        # Tree headings
        if "tree" in self._ui:
            self._configure_result_columns()
            children = self._ui["tree"].get_children()
            if len(children) == 1 and self._is_empty_row(children[0]):
                values = [""] * len(getattr(self, "_active_cols", self._COLS))
                if len(values) >= 2:
                    values[1] = _t(self._lang, "empty_title")
                if len(values) >= 3:
                    values[2] = _t(self._lang, "empty_hint")
                self._ui["tree"].item(children[0], values=tuple(values))
        if "log_tree" in self._ui:
            self._ui["log_tree"].heading("ts",  text=_t(self._lang, "col_ts"))
            self._ui["log_tree"].heading("msg", text=_t(self._lang, "col_msg"))
        if "hdr_tree" in self._ui:
            self._ui["hdr_tree"].heading("name",  text=_t(self._lang, "col_name"))
            self._ui["hdr_tree"].heading("value", text=_t(self._lang, "col_value"))

        # Numeric/advanced labels
        for key in ("max_js","max_depth","max_workers","timeout","request_delay","recursive_depth","dynamic_wait","dynamic_events","dynamic_action_limit","dynamic_scroll_steps","dynamic_recursive_limit","dynamic_script_body_limit"):
            wkey = f"lbl_{key}"
            if wkey in self._ui:
                self._ui[wkey].configure(text=_t(self._lang, key))
        for key in ("proxy","excluded_sub","js_dir"):
            wkey = f"lbl_adv_{key}"
            if wkey in self._ui:
                self._ui[wkey].configure(text=_t(self._lang, key))

        # Filter labels
        for key in ("quantity","url_type","status_code"):
            wkey = f"filter_lbl_{key}"
            if wkey in self._ui:
                self._ui[wkey].configure(text=_t(self._lang, key) + ":")

        # Checkboxes
        for key in ("recursive_scan","include_subdomains","skip_probe","verify_ssl","dynamic_analysis","dynamic_actions"):
            wkey = f"chk_{key}"
            if wkey in self._ui:
                try: self._ui[wkey].configure(text=_t(self._lang, key))
                except Exception: pass

        # Language selector text
        if "lang_lbl" in self._ui:
            self._ui["lang_lbl"].configure(text=_t(self._lang, "language"))

        # State text
        if self._state:
            self._state_text.set(_t(self._lang, self._state))
        self._update_runtime_labels()

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_closing(self) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None
        thread = self._scan_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        try:
            self.destroy()
        except Exception:
            pass


# ── Entry point ───────────────────────────────────────────────────────────────

def run_customtkinter_gui(
    initial_url: Optional[str] = None,
    initial_output: Optional[str] = None,
    initial_js_output_dir: Optional[str] = None,
) -> int:
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    app = CtkDiscoveryApp(
        initial_url=initial_url,
        initial_output=initial_output,
        initial_js_output_dir=initial_js_output_dir,
    )
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_customtkinter_gui())
