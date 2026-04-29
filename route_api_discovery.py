#!/usr/bin/env python3
"""Route discovery utility for pages and API endpoints."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
from html import escape as html_escape
import ipaddress
import json
import re
import socket
import sys
import threading
import time
import traceback
import zipfile
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Deque, Dict, Iterable, List, Optional, Sequence, Set, Tuple
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener, urlopen
from xml.sax.saxutils import escape as xml_escape


USER_AGENT = "RouteApiDiscovery/1.0"
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
}
SUPPORTED_OUTPUT_SUFFIXES = {"", ".json", ".xlsx", ".html"}
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
HOSTNAME_LABEL_RE = re.compile(r"^[A-Za-z0-9-]+$")
ASSET_EXTENSIONS = {
    ".js",
    ".mjs",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".webp",
    ".avif",
    ".mp4",
    ".webm",
    ".mp3",
    ".wav",
    ".pdf",
    ".zip",
    ".rar",
    ".7z",
    ".txt",
    ".xml",
}
STATIC_PREFIXES = ("/_next/", "/static/", "/assets/", "/public/", "/images/", "/img/", "/fonts/")
JS_HINT_PREFIXES = ("/_next/", "/static/", "/assets/")
COMMON_COUNTRY_CODE_SECOND_LEVEL_LABELS = {
    "ac",
    "co",
    "com",
    "edu",
    "go",
    "gov",
    "gr",
    "mil",
    "ne",
    "net",
    "or",
    "org",
    "re",
}
URL_SCHEME_ONLY_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*:(?:/*)?$")
INVALID_URL_CHARS_RE = re.compile(r"[\x00-\x20<>{}|\\]")
QUOTED_PATH_RE = re.compile(
    r"""(?P<quote>["'`])(?P<value>(?:https?://[^"'`]+|/[^"'`]+|[A-Za-z0-9._~\-]+/[^"'`]+|api/[^"'`]+))(?P=quote)""",
    re.IGNORECASE,
)
JS_IMPORT_RE_LIST = (
    re.compile(r"""(?P<quote>["'`])(?P<value>[^"'`]+?\.m?js(?:\?[^"'`]*)?)(?P=quote)""", re.IGNORECASE),
    re.compile(r"""import\(\s*(?P<quote>["'`])(?P<value>[^"'`]+)(?P=quote)\s*\)""", re.IGNORECASE),
    re.compile(r"""from\s+(?P<quote>["'`])(?P<value>[^"'`]+)(?P=quote)""", re.IGNORECASE),
)
API_PATTERN_RE_LIST = (
    re.compile(r"""fetch\(\s*(?P<quote>["'`])(?P<value>[^"'`]+)(?P=quote)""", re.IGNORECASE),
    re.compile(r"""axios\.(?:get|post|put|patch|delete|request)\(\s*(?P<quote>["'`])(?P<value>[^"'`]+)(?P=quote)""", re.IGNORECASE),
    re.compile(r"""url\s*:\s*(?P<quote>["'`])(?P<value>[^"'`]+)(?P=quote)""", re.IGNORECASE),
    re.compile(r"""\.open\(\s*(?P<quote>["'`])[A-Z]+(?P=quote)\s*,\s*(?P<quote2>["'`])(?P<value>[^"'`]+)(?P=quote2)""", re.IGNORECASE),
    re.compile(r"""baseURL\s*:\s*(?P<quote>["'`])(?P<value>[^"'`]+)(?P=quote)""", re.IGNORECASE),
    re.compile(r"""(?P<quote>["'`])(?P<value>/(?:api|graphql|rest)/[^"'`]*) (?P=quote)""".replace(" ", ""), re.IGNORECASE),
)
SCRIPT_BLOCK_RE = re.compile(r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.IGNORECASE | re.DOTALL)
SCRIPT_SRC_RE = re.compile(r"""\bsrc\s*=\s*(?P<quote>["']?)(?P<value>[^"' >]+)(?P=quote)""", re.IGNORECASE)
HARD_CODED_EMAIL_RE = re.compile(
    r"(?<![\w.+-])(?P<value>[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,24})(?![\w.-])"
)
HARD_CODED_PHONE_RE = re.compile(
    r"(?<![\w@])(?P<value>(?:\+82[-.\s]?)?0?(?:10|11|16|17|18|19|2|31|32|33|41|42|43|44|51|52|53|54|55|61|62|63|64|70)"
    r"(?:[-.\s]?\d{3,4})[-.\s]?\d{4}|(?:\+|00)\d{1,3}(?:[-.\s]?\(?\d{1,4}\)?){2,5})(?!\w)"
)
HARD_CODED_KEY_VALUE_RE = re.compile(
    r"""(?:(?P<kq>["'`])?(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P=kq)?)\s*[:=]\s*(?P<vq>["'`])(?P<value>[^"'`\r\n]{0,256}?)(?P=vq)""",
    re.IGNORECASE,
)
HARD_CODED_EMAIL_PLACEHOLDER_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "test.com",
    "sample.com",
    "invalid",
    "localhost",
    "local",
}
HARD_CODED_PLACEHOLDER_VALUES = {
    "",
    "test",
    "sample",
    "dummy",
    "example",
    "guest",
    "admin",
    "user",
    "root",
    "changeme",
    "your_password",
    "password",
    "000000",
    "00000000",
    "0000000000",
    "000-0000-0000",
    "010-0000-0000",
    "test@test.com",
    "your@email.com",
    "noreply@example.com",
}
HARD_CODED_DYNAMIC_VALUE_MARKERS = (
    "${",
    "{{",
    "process.env",
    "import.meta.env",
    "window.__env",
    "window.__ENV",
    "config.",
)
HARD_CODED_NAME_KEYS = {
    "fullname",
    "displayname",
    "contactname",
    "ownername",
    "managername",
}
HARD_CODED_ACCOUNT_ID_KEYS = {
    "accountid",
    "account_id",
    "memberid",
    "customerid",
    "employeeid",
}
HARD_CODED_USER_ID_KEYS = {
    "userid",
    "user_id",
    "loginid",
    "login_id",
    "username",
    "login",
}
HARD_CODED_CREDENTIAL_KEYS = {"password", "passwd", "pwd", "pin"}
HARD_CODED_TOKEN_KEYS = {
    "token",
    "accesstoken",
    "refreshtoken",
    "apikey",
    "api_key",
    "secret",
    "clientsecret",
    "authorization",
    "bearer",
}
HARD_CODED_EMAIL_KEYS = {"email", "loginemail", "contactemail"}
HARD_CODED_PHONE_KEYS = {"phone", "mobile", "tel", "telephone", "contactphone"}
HARD_CODED_PII_CATEGORIES = {"email", "phone", "person_name", "account_id", "user_id"}
HARD_CODED_SECRET_CATEGORIES = {"credential", "token"}
HARD_CODED_ALL_CATEGORIES = ("email", "phone", "person_name", "account_id", "user_id", "credential", "token")
HARD_CODED_SEVERITY_LEVELS = ("critical", "high", "medium", "low")
HARD_CODED_LINE_CONTEXT_RADIUS = 60
HARD_CODED_PHONE_CONTEXT_HINTS = ("phone", "mobile", "tel", "contact", "call")

ProgressCallback = Optional[Callable[[str], None]]
CANCEL_MESSAGE = "사용자 요청으로 스캔을 중지했습니다."


class ScanCancelled(RuntimeError):
    """Raised when the active scan has been cancelled by the user."""


@dataclass
class Config:
    url: str
    max_js_files: int
    max_depth: int
    timeout: float
    output: Path
    skip_probe: bool
    recursive_scan: bool = False
    recursive_depth: int = 1
    include_subdomains: bool = True
    excluded_subdomains: Tuple[str, ...] = ()
    max_workers: int = 1
    request_delay: float = 0.0
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    proxy_url: str = ""
    js_output_dir: Optional[Path] = None


@dataclass
class RequestThrottle:
    delay_seconds: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _next_request_time: float = field(default=0.0, repr=False)

    def wait_for_turn(self, cancel_event: Optional[threading.Event] = None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise ScanCancelled(CANCEL_MESSAGE)
        if self.delay_seconds <= 0:
            return
        with self._lock:
            now = time.monotonic()
            scheduled_time = max(now, self._next_request_time)
            self._next_request_time = scheduled_time + self.delay_seconds
        while True:
            remaining_seconds = scheduled_time - time.monotonic()
            if remaining_seconds <= 0:
                return
            wait_seconds = min(remaining_seconds, 0.1)
            if cancel_event is None:
                time.sleep(wait_seconds)
                continue
            if cancel_event.wait(wait_seconds):
                raise ScanCancelled(CANCEL_MESSAGE)


@dataclass
class ExecutionContext:
    max_workers: int
    request_throttle: RequestThrottle
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)


@dataclass
class FetchResult:
    url: str
    status_code: Optional[int]
    text: str
    success: bool
    length: int
    error: Optional[str] = None
    content_type: Optional[str] = None


@dataclass
class Candidate:
    url: str
    path: str
    kind: str
    sources: Set[str] = field(default_factory=set)


@dataclass(frozen=True)
class UrlScope:
    hostname: str
    site_hostname: str
    include_subdomains: bool = True
    excluded_hostnames: Tuple[str, ...] = ()


@dataclass
class ProbeResult:
    accessible: Optional[bool]
    status_code: Optional[int]
    method: Optional[str]
    error: Optional[str]
    length: int = 0


@dataclass
class SheetSpec:
    name: str
    rows: List[List[object]]


@dataclass
class RecursiveDiscoveryState:
    known_js_urls: Set[str] = field(default_factory=set)
    known_page_paths: Set[str] = field(default_factory=set)
    known_api_paths: Set[str] = field(default_factory=set)
    scanned_target_paths: Set[str] = field(default_factory=set)
    scanned_target_urls: List[str] = field(default_factory=list)
    discovered_target_paths: Set[str] = field(default_factory=set)
    discovered_target_urls: List[str] = field(default_factory=list)
    skipped_js_duplicates: int = 0
    skipped_page_duplicates: int = 0
    skipped_api_duplicates: int = 0
    skipped_target_duplicates: int = 0


class ScriptHtmlParser:
    def __init__(self) -> None:
        self.script_srcs: List[str] = []
        self.inline_scripts: List[str] = []

    def feed(self, html: str) -> None:
        self.script_srcs.clear()
        self.inline_scripts.clear()

        for match in SCRIPT_BLOCK_RE.finditer(html):
            attrs = match.group("attrs") or ""
            body = (match.group("body") or "").strip()
            src_match = SCRIPT_SRC_RE.search(attrs)
            if src_match:
                self.script_srcs.append(src_match.group("value"))
            elif body:
                self.inline_scripts.append(body)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HTML과 JavaScript에서 페이지 경로와 API 엔드포인트를 추출합니다.")
    parser.add_argument("--gui", action="store_true", help="PySide6 GUI를 엽니다.")
    parser.add_argument("url", nargs="?", help="검사할 대상 URL")
    parser.add_argument("--max-js-files", type=int, default=50, help="가져올 JS 파일의 최대 개수(기본값: 50)")
    parser.add_argument("--max-depth", type=int, default=2, help="재귀 JS 탐색의 최대 깊이(기본값: 2)")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP 타임아웃(초, 기본값: 15)")
    parser.add_argument("--output", type=Path, default=Path("discovery-result.json"), help="결과 파일 경로(.json/.xlsx/.html 또는 확장자 없음, 기본값: discovery-result.json)")
    parser.add_argument("--skip-probe", action="store_true", help="추출된 경로의 접근성 확인을 건너뜁니다.")
    parser.add_argument("--recursive-scan", action="store_true", help="접근 가능한 페이지(200)를 대상으로 재귀 탐색을 수행합니다.")
    parser.add_argument("--recursive-depth", type=int, default=1, help="재귀 탐색 단계(기본값: 1)")
    parser.add_argument(
        "--include-subdomains",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="동일 사이트의 서브도메인까지 스캔 범위에 포함합니다(기본값: 사용, `--no-include-subdomains`로 해제).",
    )
    parser.add_argument(
        "--exclude-subdomains",
        action="append",
        default=[],
        metavar="HOST[,HOST...]",
        help="탐색에서 제외할 서브도메인 호스트 목록입니다. 쉼표로 여러 개를 입력할 수 있습니다.",
    )

    parser.add_argument("--max-workers", type=int, default=1, help="동시에 처리할 최대 요청 작업 수(기본값: 1)")
    parser.add_argument("--request-delay", type=float, default=0.0, help="요청 시작 간 최소 딜레이(초, 기본값: 0)")
    parser.add_argument("--proxy", type=str, default="", help="프록시 URL(http://host:port 또는 https://host:port)")
    parser.add_argument("--save-js-dir", type=Path, default=None, help="가져온 JS 파일 본문을 저장할 디렉터리")
    parser.add_argument("--no-verify-ssl", action="store_true", help="SSL 인증서 검증을 건너뜁니다(자체 서명 인증서 허용).")
    parser.add_argument("--debug", action="store_true", help="오류 발생 시 traceback을 함께 출력합니다.")

    args = parser.parse_args(argv)
    if not args.gui and not args.url:
        parser.error("`--gui`를 사용하지 않는 경우 URL 인자가 필요합니다.")
    return args


def build_config(args: argparse.Namespace) -> Config:
    config = Config(
        url=args.url,
        max_js_files=max(1, args.max_js_files),
        max_depth=max(0, args.max_depth),
        timeout=max(1.0, args.timeout),
        output=args.output,
        skip_probe=args.skip_probe,
        recursive_scan=args.recursive_scan,
        recursive_depth=max(0, args.recursive_depth),
        include_subdomains=bool(args.include_subdomains),
        excluded_subdomains=parse_hostname_filters(args.exclude_subdomains),
        max_workers=max(1, args.max_workers),
        request_delay=max(0.0, args.request_delay),
        verify_ssl=not args.no_verify_ssl,
        proxy_url=str(args.proxy or "").strip(),
        js_output_dir=args.save_js_dir,
    )
    validate_config(config)
    return config


def validate_config(config: Config) -> None:
    if config.recursive_scan and config.skip_probe:
        raise ValueError("재귀 탐색은 프로브 생략과 함께 사용할 수 없습니다. 프로브 생략을 해제하거나 재귀 탐색을 끄고 다시 시도해 주세요.")


    if config.max_workers < 1:
        raise ValueError("동시 요청 수는 1 이상이어야 합니다.")
    if config.max_workers > 32:
        raise ValueError("동시 요청 수는 32 이하로 설정해 주세요.")
    if config.request_delay < 0:
        raise ValueError("요청 딜레이는 0 이상이어야 합니다.")
    validate_proxy_url(config.proxy_url)
    validate_output_path(config.output)
    validate_js_output_dir(config.js_output_dir)


def validate_output_path(output: Path) -> None:
    suffix = output.suffix.lower()
    if suffix not in SUPPORTED_OUTPUT_SUFFIXES:
        raise ValueError("지원하지 않는 출력 형식입니다. `.json`, `.xlsx`, `.html`, 또는 확장자 없이 입력해 주세요.")


def validate_js_output_dir(output_dir: Optional[Path]) -> None:
    if output_dir is None:
        return
    path = Path(output_dir).expanduser()
    for part in path.parts:
        if part in {path.anchor, path.drive, path.root}:
            continue
        if is_windows_reserved_filename(part):
            raise ValueError("JS 저장 경로에 Windows 예약 이름을 사용할 수 없습니다.")
    if path.exists() and not path.is_dir():
        raise ValueError("JS 저장 경로는 디렉터리여야 합니다.")


def validate_proxy_url(proxy_url: str) -> None:
    value = str(proxy_url or "").strip()
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise ValueError("프록시 URL은 `http://host:port` 또는 `https://host:port` 형식이어야 합니다.")


WINDOWS_RESERVED_FILENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def normalize_js_output_dir(output_dir: Optional[Path]) -> Optional[Path]:
    if output_dir is None:
        return None
    return Path(output_dir).expanduser().resolve()


def is_windows_reserved_filename(value: str) -> bool:
    name = str(value or "").strip().rstrip(" .")
    if not name:
        return False
    return name.split(".", 1)[0].upper() in WINDOWS_RESERVED_FILENAMES


def build_saved_js_filename(script_url: str, sequence: int) -> str:
    parsed = urlparse(script_url)
    raw_name = Path(parsed.path).name or "script.js"
    suffix = Path(raw_name).suffix.lower()
    if suffix not in {".js", ".mjs"}:
        suffix = ".js"

    stem = Path(raw_name).stem if Path(raw_name).stem else "script"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "script"
    if is_windows_reserved_filename(stem):
        stem = f"file_{stem}"
    stem = stem[:80]
    digest = hashlib.sha256(script_url.encode("utf-8")).hexdigest()[:12]
    return f"{sequence:04d}_{stem}_{digest}{suffix}"


def save_js_file(script_url: str, text: str, output_dir: Path, sequence: int) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = build_saved_js_filename(script_url, sequence)
    path = output_dir / filename
    path.write_text(text, encoding="utf-8")
    return path.resolve()


def build_execution_context(config: Config) -> ExecutionContext:
    return ExecutionContext(
        max_workers=max(1, config.max_workers),
        request_throttle=RequestThrottle(delay_seconds=max(0.0, config.request_delay)),
    )


def ensure_not_cancelled(execution: Optional[ExecutionContext]) -> None:
    if execution is not None and execution.cancel_event.is_set():
        raise ScanCancelled(CANCEL_MESSAGE)


def _contains_invalid_header_value_chars(value: str) -> bool:
    return any((ord(character) < 32 and character != "\t") or ord(character) == 127 for character in value)


def parse_header_lines(text: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"{line_number}번째 줄의 형식이 올바르지 않습니다. `Header-Name: value` 형식으로 입력해 주세요.")
        name, value = line.split(":", 1)
        name = name.strip()
        value = value.lstrip()
        if not name:
            raise ValueError(f"{line_number}번째 줄의 헤더 이름이 비어 있습니다.")
        if not HEADER_NAME_RE.fullmatch(name):
            raise ValueError(f"{line_number}번째 줄의 헤더 이름이 올바르지 않습니다: {name}")
        if _contains_invalid_header_value_chars(value):
            raise ValueError(f"{line_number}번째 줄의 헤더 값에 제어 문자를 포함할 수 없습니다.")
        headers[name] = value
    return headers


def parse_hostname_filters(values: Optional[Sequence[str]]) -> Tuple[str, ...]:
    if not values:
        return ()

    hostnames: List[str] = []
    seen: Set[str] = set()
    for raw_value in values:
        for token in re.split(r"[\s,;]+", str(raw_value or "").strip()):
            if not token:
                continue

            normalized = normalize_hostname(token)
            if normalized.startswith("*."):
                normalized = normalized[2:]
            if not normalized:
                continue
            if any(character in normalized for character in ("://", "/", "?", "#", "@", ":")):
                raise ValueError(f"제외할 서브도메인은 호스트명만 입력해 주세요: {token}")

            labels = normalized.split(".")
            if any(not label or label.startswith("-") or label.endswith("-") or not HOSTNAME_LABEL_RE.fullmatch(label) for label in labels):
                raise ValueError(f"제외할 서브도메인 형식이 올바르지 않습니다: {token}")

            if normalized in seen:
                continue
            seen.add(normalized)
            hostnames.append(normalized)
    return tuple(hostnames)


def parse_input_urls(text: str) -> List[str]:
    urls: List[str] = []
    seen: Set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        url = raw_line.strip()
        if not url:
            continue
        if not is_scan_target_url(url):
            raise ValueError(f"{line_number}번째 줄의 URL이 올바르지 않습니다: {url}")
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)

    if not urls:
        raise ValueError("최소 1개의 URL을 입력해 주세요.")
    return urls


def merge_request_headers(user_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    merged: Dict[str, str] = dict(DEFAULT_REQUEST_HEADERS)
    if not user_headers:
        return merged

    lower_to_key = {key.lower(): key for key in merged}
    for key, value in user_headers.items():
        existing_key = lower_to_key.get(key.lower())
        if existing_key is not None:
            merged[existing_key] = value
        else:
            merged[key] = value
            lower_to_key[key.lower()] = key
    return merged


def build_empty_scan_result(config: Config, url: str, error: str, status: str = "error") -> dict:
    scanned_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    hardcoded_summary_fields = build_hardcoded_summary_fields([])
    return {
        "input_url": url,
        "scanned_at": scanned_at,
        "origin": get_origin_key(url),
        "probe_skipped": config.skip_probe,
        "include_subdomains": config.include_subdomains,
        "excluded_subdomains": list(config.excluded_subdomains),
        "max_js_files": config.max_js_files,
        "max_depth": config.max_depth,
        "max_workers": config.max_workers,
        "request_delay": config.request_delay,
        "proxy_url": config.proxy_url,
        "js_output_dir": str(normalize_js_output_dir(config.js_output_dir) or ""),
        "status": status,
        "error": error,
        "recursive_enabled": config.recursive_scan,
        "recursive_depth": config.recursive_depth if config.recursive_scan else 0,
        "recursive_scanned_targets": [url],
        "recursive_discovered_targets": [],
        "recursive_total_scans": 1,
        "recursive_failed_targets": [{"target_url": url, "depth": 0, "error": error}],
        "recursive_dedupe": {"js": 0, "pages": 0, "apis": 0, "targets": 0},
        "js_files": [],
        "accessible_pages": [],
        "accessible_apis": [],
        "all_pages": [],
        "all_apis": [],
        "hardcoded_findings": [],
        "hardcoded_summary": summarize_hardcoded_findings([]),
        "sensitive_findings": [],
        "sensitive_summary": summarize_hardcoded_findings([]),
        "summary": {
            "js_discovered": 0,
            "js_fetched": 0,
            "js_saved": 0,
            "page_count": 0,
            "api_count": 0,
            **hardcoded_summary_fields,
        },
    }


def decorate_scan_result(result: dict, scan_index: int, scan_total: int, status: str = "success") -> dict:
    decorated = dict(result)
    decorated["status"] = status
    decorated["scan_index"] = scan_index
    decorated["scan_total"] = scan_total
    return decorated


def build_batch_result(records: List[dict], input_urls: List[str], config: Config) -> dict:
    success_count = sum(1 for record in records if record.get("status") == "success")
    failed_count = len(records) - success_count
    totals = {
        "js_discovered": 0,
        "js_fetched": 0,
        "js_saved": 0,
        "page_count": 0,
        "api_count": 0,
        "hardcoded_total": 0,
        "hardcoded_high_or_above": 0,
        "hardcoded_pii_count": 0,
        "hardcoded_secret_count": 0,
        "sensitive_total": 0,
        "sensitive_high_or_above": 0,
        "sensitive_pii_count": 0,
        "sensitive_secret_count": 0,
    }
    for record in records:
        summary = record.get("summary") or {}
        totals["js_discovered"] += int(summary.get("js_discovered", 0) or 0)
        totals["js_fetched"] += int(summary.get("js_fetched", 0) or 0)
        totals["js_saved"] += int(summary.get("js_saved", 0) or 0)
        totals["page_count"] += int(summary.get("page_count", 0) or 0)
        totals["api_count"] += int(summary.get("api_count", 0) or 0)
        totals["hardcoded_total"] += summary_count(summary, "hardcoded_total", "sensitive_total")
        totals["hardcoded_high_or_above"] += summary_count(summary, "hardcoded_high_or_above", "sensitive_high_or_above")
        totals["hardcoded_pii_count"] += summary_count(summary, "hardcoded_pii_count", "sensitive_pii_count")
        totals["hardcoded_secret_count"] += summary_count(summary, "hardcoded_secret_count", "sensitive_secret_count")
        totals["sensitive_total"] += summary_count(summary, "sensitive_total", "hardcoded_total")
        totals["sensitive_high_or_above"] += summary_count(summary, "sensitive_high_or_above", "hardcoded_high_or_above")
        totals["sensitive_pii_count"] += summary_count(summary, "sensitive_pii_count", "hardcoded_pii_count")
        totals["sensitive_secret_count"] += summary_count(summary, "sensitive_secret_count", "hardcoded_secret_count")

    recursive_total_scans = 0
    recursive_discovered_target_count = 0
    recursive_failed_target_count = 0
    dedupe_totals = {"js": 0, "pages": 0, "apis": 0, "targets": 0}
    for record in records:
        recursive_total_scans += int(record.get("recursive_total_scans", 1) or 1)
        recursive_discovered_target_count += len(record.get("recursive_discovered_targets", []) or [])
        recursive_failed_target_count += len(record.get("recursive_failed_targets", []) or [])
        dedupe = record.get("recursive_dedupe") or {}
        dedupe_totals["js"] += int(dedupe.get("js", 0) or 0)
        dedupe_totals["pages"] += int(dedupe.get("pages", 0) or 0)
        dedupe_totals["apis"] += int(dedupe.get("apis", 0) or 0)
        dedupe_totals["targets"] += int(dedupe.get("targets", 0) or 0)

    return {
        "input_urls": input_urls,
        "scanned_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "probe_skipped": config.skip_probe,
        "include_subdomains": config.include_subdomains,
        "excluded_subdomains": list(config.excluded_subdomains),
        "recursive_enabled": config.recursive_scan,
        "recursive_depth": config.recursive_depth if config.recursive_scan else 0,
        "max_js_files": config.max_js_files,
        "max_depth": config.max_depth,
        "max_workers": config.max_workers,
        "request_delay": config.request_delay,
        "proxy_url": config.proxy_url,
        "js_output_dir": str(normalize_js_output_dir(config.js_output_dir) or ""),
        "result_count": len(records),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": records,
        "summary": {
            **totals,
            "input_url_count": len(input_urls),
            "result_count": len(records),
            "success_count": success_count,
            "failed_count": failed_count,
            "recursive_total_scans": recursive_total_scans,
            "recursive_discovered_target_count": recursive_discovered_target_count,
            "recursive_failed_target_count": recursive_failed_target_count,
            "recursive_dedupe": dedupe_totals,
        },
    }


def _is_disallowed_host(hostname: str) -> bool:
    normalized = hostname.strip().lower()
    if not normalized:
        return True
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        parsed_ip = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return not parsed_ip.is_global


def is_http_url(value: str, *, allow_disallowed_host: bool = False) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    hostname = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not hostname:
        return False
    return allow_disallowed_host or not _is_disallowed_host(hostname)


def is_scan_target_url(value: str) -> bool:
    return is_http_url(value, allow_disallowed_host=True)


def should_allow_disallowed_host(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    hostname = parsed.hostname or ""
    return bool(hostname) and _is_disallowed_host(hostname)


def resolve_absolute_url(base_url: str, candidate: str, *, allow_disallowed_host: bool = False) -> Optional[str]:
    value = candidate.strip()
    if not value:
        return None
    if URL_SCHEME_ONLY_RE.match(value):
        return None
    lowered = value.lower()
    if lowered.startswith(("javascript:", "data:", "mailto:", "tel:", "#")):
        return None
    if value == "//":
        return None
    if INVALID_URL_CHARS_RE.search(value):
        return None
    try:
        absolute = urljoin(base_url, value)
    except ValueError:
        return None
    if not is_http_url(absolute, allow_disallowed_host=allow_disallowed_host):
        return None
    return absolute


def normalize_path(value: str) -> str:
    parsed = urlparse(value)
    path = parsed.path or "/"
    if parsed.query:
        return f"{path}?{parsed.query}"
    return path


def get_origin_key(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_hostname(hostname: str) -> str:
    return (hostname or "").strip().strip(".").lower()


def get_hostname_key(url: str) -> str:
    parsed = urlparse(url)
    return normalize_hostname(parsed.hostname or parsed.netloc)


def get_site_hostname_key(hostname: str) -> str:
    host = normalize_hostname(hostname)
    if not host:
        return ""
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return host
    if host == "localhost":
        return host

    labels = [label for label in host.split(".") if label]
    if len(labels) <= 2:
        return ".".join(labels)
    if len(labels[-1]) == 2 and labels[-2] in COMMON_COUNTRY_CODE_SECOND_LEVEL_LABELS:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def get_domain_key(url: str) -> str:
    return get_site_hostname_key(get_hostname_key(url))


def build_url_scope(
    url: str,
    include_subdomains: bool = True,
    excluded_hostnames: Sequence[str] = (),
) -> UrlScope:
    hostname = get_hostname_key(url)
    return UrlScope(
        hostname=hostname,
        site_hostname=get_site_hostname_key(hostname),
        include_subdomains=include_subdomains,
        excluded_hostnames=tuple(normalize_hostname(item) for item in excluded_hostnames if normalize_hostname(item)),
    )


def is_hostname_excluded(hostname: str, excluded_hostnames: Sequence[str]) -> bool:
    normalized = normalize_hostname(hostname)
    if not normalized:
        return False
    for excluded in excluded_hostnames:
        blocked = normalize_hostname(excluded)
        if not blocked:
            continue
        if normalized == blocked or normalized.endswith(f".{blocked}"):
            return True
    return False


def url_matches_scope(url: str, scope: UrlScope) -> bool:
    hostname = get_hostname_key(url)
    if not hostname:
        return False
    if hostname != scope.hostname and is_hostname_excluded(hostname, scope.excluded_hostnames):
        return False
    if scope.include_subdomains:
        return get_site_hostname_key(hostname) == scope.site_hostname
    return hostname == scope.hostname


def read_response_text(response) -> str:
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("응답 크기 제한(10 MB)을 초과했습니다.")
    charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def response_length(response, text: str) -> int:
    if text:
        return len(text)
    content_length = response.headers.get("Content-Length")
    if content_length is None:
        return 0
    try:
        return max(0, int(content_length))
    except (TypeError, ValueError):
        return 0


def fetch_text(
    url: str,
    timeout: float,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    verify_ssl: bool = True,
    proxy_url: str = "",
) -> FetchResult:
    ensure_not_cancelled(execution)
    try:
        request = Request(
            url=url,
            headers=merge_request_headers(headers),
            method=method,
        )
    except ValueError as exc:
        return FetchResult(url=url, status_code=None, text="", success=False, length=0, error=str(exc))

    ssl_context: Optional[ssl.SSLContext] = None
    if not verify_ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    proxy = str(proxy_url or "").strip()

    try:
        if execution is not None:
            execution.request_throttle.wait_for_turn(cancel_event=execution.cancel_event)
            ensure_not_cancelled(execution)
        if proxy:
            proxy_handlers = [ProxyHandler({"http": proxy, "https": proxy})]
            if ssl_context is not None:
                proxy_handlers.append(HTTPSHandler(context=ssl_context))
            opener = build_opener(*proxy_handlers)
            request_context = opener.open(request, timeout=timeout)
        else:
            request_context = urlopen(request, timeout=timeout, context=ssl_context)
        with request_context as response:
            text = read_response_text(response)
            return FetchResult(
                url=url,
                status_code=response.getcode(),
                text=text,
                success=True,
                length=response_length(response, text),
                content_type=response.headers.get("Content-Type"),
            )
    except HTTPError as exc:
        error_text = ""
        error_message = str(exc)
        try:
            error_text = read_response_text(exc)
        except Exception as body_exc:
            error_message = f"{exc} / {body_exc}"
            error_text = ""
        finally:
            exc.close()
        return FetchResult(
            url=url,
            status_code=exc.code,
            text=error_text,
            success=False,
            length=len(error_text),
            error=error_message,
            content_type=exc.headers.get("Content-Type"),
        )
    except URLError as exc:
        return FetchResult(url=url, status_code=None, text="", success=False, length=0, error=str(exc.reason))
    except (socket.timeout, TimeoutError, ssl.SSLError, OSError, ValueError) as exc:
        return FetchResult(
            url=url,
            status_code=None,
            text="",
            success=False,
            length=0,
            error=str(exc) or exc.__class__.__name__,
        )


def emit_progress(progress: ProgressCallback, message: str) -> None:
    if progress is not None:
        progress(message)


def should_follow_js(candidate: str) -> bool:
    parsed = urlparse(candidate)
    path = parsed.path.lower()
    return path.endswith(".js") or path.endswith(".mjs") or path.startswith(JS_HINT_PREFIXES)


def is_static_asset(path: str) -> bool:
    lowered = urlparse(path).path.lower()
    if lowered.startswith(STATIC_PREFIXES):
        return True
    return any(lowered.endswith(extension) for extension in ASSET_EXTENSIONS)


def classify_candidate(raw_value: str, absolute_url: str) -> str:
    path = normalize_path(absolute_url)
    raw_lowered = raw_value.lower()
    path_lowered = path.lower()
    if (
        path_lowered.startswith("/api")
        or "/graphql" in path_lowered
        or "/rest" in path_lowered
        or raw_lowered.startswith(("api/", "v1/", "v2/", "v3/"))
    ):
        return "api"
    return "page"


def add_candidate(bucket: Dict[str, Candidate], absolute_url: str, source: str, kind: str) -> None:
    path = normalize_path(absolute_url)
    candidate = bucket.get(path)
    if candidate is None:
        candidate = Candidate(url=absolute_url, path=path, kind=kind)
        bucket[path] = candidate
    candidate.sources.add(source)


def collect_path_candidates(
    text: str,
    base_url: str,
    source_label: str,
    scope: UrlScope,
    page_bucket: Dict[str, Candidate],
    api_bucket: Dict[str, Candidate],
) -> None:
    allow_disallowed_host = should_allow_disallowed_host(base_url)
    for match in QUOTED_PATH_RE.finditer(text):
        raw_value = match.group("value").strip()
        absolute = resolve_absolute_url(base_url, raw_value, allow_disallowed_host=allow_disallowed_host)
        if not absolute:
            continue
        if not url_matches_scope(absolute, scope):
            continue
        path = normalize_path(absolute)
        if path == "/" or is_static_asset(path):
            continue
        kind = classify_candidate(raw_value, absolute)
        if kind == "api":
            add_candidate(api_bucket, absolute, source_label, "api")
        else:
            add_candidate(page_bucket, absolute, source_label, "page")

    for pattern in API_PATTERN_RE_LIST:
        for match in pattern.finditer(text):
            raw_value = match.group("value").strip()
            absolute = resolve_absolute_url(base_url, raw_value, allow_disallowed_host=allow_disallowed_host)
            if not absolute:
                continue
            if not url_matches_scope(absolute, scope):
                continue
            path = normalize_path(absolute)
            if is_static_asset(path):
                continue
            add_candidate(api_bucket, absolute, source_label, "api")


def extract_html_assets(html: str, page_url: str, scope: UrlScope) -> Tuple[List[str], List[str]]:
    parser = ScriptHtmlParser()
    parser.feed(html)

    script_urls: List[str] = []
    allow_disallowed_host = should_allow_disallowed_host(page_url)
    for script_src in parser.script_srcs:
        absolute = resolve_absolute_url(page_url, script_src, allow_disallowed_host=allow_disallowed_host)
        # Anything declared in <script src> should be treated as a JS fetch
        # target, even when the URL itself omits a .js suffix.
        if absolute and url_matches_scope(absolute, scope):
            script_urls.append(absolute)
    return script_urls, parser.inline_scripts


def extract_additional_js_urls(script_text: str, source_url: str, scope: UrlScope) -> List[str]:
    discovered: List[str] = []
    allow_disallowed_host = should_allow_disallowed_host(source_url)
    for pattern in JS_IMPORT_RE_LIST:
        for match in pattern.finditer(script_text):
            raw_value = match.group("value").strip()
            absolute = resolve_absolute_url(source_url, raw_value, allow_disallowed_host=allow_disallowed_host)
            if absolute and url_matches_scope(absolute, scope) and should_follow_js(absolute):
                discovered.append(absolute)
    return discovered


def _normalize_hardcoded_field_name(field_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(field_name or "").strip().lower())


def _line_column_from_offset(text: str, index: int) -> Tuple[int, int]:
    safe_index = max(0, min(index, len(text)))
    line = text.count("\n", 0, safe_index) + 1
    last_line_break = text.rfind("\n", 0, safe_index)
    if last_line_break < 0:
        column = safe_index + 1
    else:
        column = safe_index - last_line_break
    return line, column


def _extract_context_snippet(text: str, start: int, end: int, radius: int = HARD_CODED_LINE_CONTEXT_RADIUS) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return text[left:right].replace("\n", " ").replace("\r", " ").strip()


def _looks_like_dynamic_reference(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return False
    return lowered.startswith("$") or any(marker in lowered for marker in HARD_CODED_DYNAMIC_VALUE_MARKERS)


def _normalize_hardcoded_value(category: str, value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if category == "email":
        return raw.lower()
    if category == "phone":
        return re.sub(r"\D", "", raw)
    if category in {"person_name", "account_id", "user_id"}:
        return re.sub(r"\s+", " ", raw).strip().lower()
    return raw.strip()


def _is_placeholder_hardcoded_value(category: str, value: str, normalized_value: str) -> bool:
    lowered = str(value or "").strip().lower()
    normalized = str(normalized_value or "").strip().lower()
    if lowered in HARD_CODED_PLACEHOLDER_VALUES or normalized in HARD_CODED_PLACEHOLDER_VALUES:
        return True
    if category == "email" and "@" in lowered:
        domain = lowered.split("@", 1)[1]
        if domain in HARD_CODED_EMAIL_PLACEHOLDER_DOMAINS:
            return True
    if category == "phone":
        digits = re.sub(r"\D", "", lowered)
        if not digits:
            return True
        if digits in {"0" * len(digits), "1" * len(digits)}:
            return True
    if "dummy" in lowered or "sample" in lowered or "fixture" in lowered or "mock" in lowered:
        return True
    return False


def _is_valid_phone_candidate(value: str) -> bool:
    return _is_valid_phone_candidate_with_context(value, field_name="", context="")


def _has_phone_context(field_name: str, context: str) -> bool:
    normalized_field = _normalize_hardcoded_field_name(field_name)
    if normalized_field in HARD_CODED_PHONE_KEYS:
        return True
    context_lower = str(context or "").lower()
    return any(hint in context_lower for hint in HARD_CODED_PHONE_CONTEXT_HINTS)


def _is_valid_phone_candidate_with_context(value: str, field_name: str, context: str) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 8 or len(digits) > 15:
        return False
    if re.fullmatch(r"(19|20)\d{6}", digits):
        return False
    raw_lower = raw.lower()
    if raw_lower.startswith(("+", "00")) and not _has_phone_context(field_name, context):
        return False
    return True


def _is_probable_person_name(value: str) -> bool:
    raw = re.sub(r"\s+", " ", str(value or "").strip())
    if not raw:
        return False
    lowered = raw.lower()
    if lowered in {"admin", "root", "test", "guest", "user"}:
        return False
    if re.fullmatch(r"[가-힣]{2,5}", raw):
        return True
    tokens = [token for token in raw.split(" ") if token]
    if len(tokens) < 2:
        return False
    return all(bool(re.fullmatch(r"[A-Za-z][A-Za-z.'\-]{0,20}", token)) for token in tokens)


def _categorize_hardcoded_field(field_name: str, value: str) -> Optional[str]:
    normalized_key = _normalize_hardcoded_field_name(field_name)
    stripped_value = str(value or "").strip()
    if normalized_key in HARD_CODED_NAME_KEYS:
        return "person_name" if _is_probable_person_name(stripped_value) else None
    if normalized_key in HARD_CODED_EMAIL_KEYS:
        return "email" if HARD_CODED_EMAIL_RE.fullmatch(stripped_value) else None
    if normalized_key in HARD_CODED_PHONE_KEYS:
        return "phone" if _is_valid_phone_candidate_with_context(stripped_value, field_name=field_name, context=field_name) else None
    if normalized_key in HARD_CODED_ACCOUNT_ID_KEYS:
        return "account_id"
    if normalized_key in HARD_CODED_USER_ID_KEYS:
        return "user_id"
    if normalized_key in HARD_CODED_CREDENTIAL_KEYS:
        return "credential"
    if normalized_key in HARD_CODED_TOKEN_KEYS:
        return "token"
    return None


def _score_hardcoded_finding(
    category: str,
    field_name: str,
    context: str,
    source_type: str,
    is_placeholder: bool,
) -> float:
    base_confidence = {
        "email": 0.74,
        "phone": 0.72,
        "person_name": 0.65,
        "account_id": 0.73,
        "user_id": 0.75,
        "credential": 0.90,
        "token": 0.92,
    }.get(category, 0.60)
    if field_name:
        base_confidence += 0.10

    context_lower = context.lower()
    if any(keyword in context_lower for keyword in ("login", "admin", "account", "auth", "password", "token")):
        base_confidence += 0.08
    if source_type == "js":
        base_confidence += 0.05
    if is_placeholder:
        base_confidence -= 0.35
    return max(0.05, min(0.99, round(base_confidence, 3)))


def _severity_for_hardcoded_finding(category: str, confidence: float) -> str:
    if category in HARD_CODED_SECRET_CATEGORIES and confidence >= 0.80:
        return "critical"
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "medium"
    return "low"


def _append_hardcoded_finding(
    findings: List[dict],
    dedupe_keys: Set[Tuple[str, str, str, str, int, int]],
    *,
    category: str,
    field_name: str,
    value: str,
    source_type: str,
    source_url: str,
    source_label: str,
    line: int,
    column: int,
    context: str,
    matched_by: str,
) -> None:
    normalized_value = _normalize_hardcoded_value(category, value)
    if not normalized_value:
        return
    dedupe_key = (
        category,
        normalized_value,
        source_type,
        source_label,
        int(line or 0),
        int(column or 0),
    )
    if dedupe_key in dedupe_keys:
        return

    is_placeholder = _is_placeholder_hardcoded_value(category, value, normalized_value)
    confidence = _score_hardcoded_finding(
        category=category,
        field_name=field_name,
        context=context,
        source_type=source_type,
        is_placeholder=is_placeholder,
    )
    severity = _severity_for_hardcoded_finding(category, confidence)
    findings.append(
        {
            "category": category,
            "field_name": field_name,
            "value": value,
            "masked_value": value,
            "normalized_value": normalized_value,
            "source_type": source_type,
            "source_url": source_url,
            "source_label": source_label,
            "line": int(line or 0),
            "column": int(column or 0),
            "context": context,
            "confidence": confidence,
            "severity": severity,
            "matched_by": matched_by,
        }
    )
    dedupe_keys.add(dedupe_key)


def collect_hardcoded_findings(
    text: str,
    source_url: str,
    source_label: str,
    source_type: str,
    findings: List[dict],
    dedupe_keys: Set[Tuple[str, str, str, str, int, int]],
) -> None:
    if not text:
        return

    for match in HARD_CODED_KEY_VALUE_RE.finditer(text):
        field_name = (match.group("key") or "").strip()
        value = (match.group("value") or "").strip()
        if not field_name or not value:
            continue
        if _looks_like_dynamic_reference(value):
            continue

        category = _categorize_hardcoded_field(field_name, value)
        if category is None:
            continue
        start = match.start("value")
        end = match.end("value")
        context = _extract_context_snippet(text, start, end)
        if category == "email" and not HARD_CODED_EMAIL_RE.fullmatch(value):
            continue
        if category == "phone" and not _is_valid_phone_candidate_with_context(value, field_name=field_name, context=context):
            continue
        if category == "person_name" and not _is_probable_person_name(value):
            continue

        line, column = _line_column_from_offset(text, start)
        _append_hardcoded_finding(
            findings=findings,
            dedupe_keys=dedupe_keys,
            category=category,
            field_name=field_name,
            value=value,
            source_type=source_type,
            source_url=source_url,
            source_label=source_label,
            line=line,
            column=column,
            context=context,
            matched_by="key_context.literal",
        )

    for match in HARD_CODED_EMAIL_RE.finditer(text):
        value = (match.group("value") or "").strip()
        if not value:
            continue
        start = match.start("value")
        end = match.end("value")
        context = _extract_context_snippet(text, start, end)
        if "://" in context and ":" in context.split("@", 1)[0]:
            continue
        line, column = _line_column_from_offset(text, start)
        _append_hardcoded_finding(
            findings=findings,
            dedupe_keys=dedupe_keys,
            category="email",
            field_name="",
            value=value,
            source_type=source_type,
            source_url=source_url,
            source_label=source_label,
            line=line,
            column=column,
            context=context,
            matched_by="regex.email",
        )

    for match in HARD_CODED_PHONE_RE.finditer(text):
        value = (match.group("value") or "").strip()
        if not value:
            continue
        start = match.start("value")
        end = match.end("value")
        context = _extract_context_snippet(text, start, end)
        if _looks_like_dynamic_reference(value) or not _is_valid_phone_candidate_with_context(value, field_name="", context=context):
            continue
        line, column = _line_column_from_offset(text, start)
        _append_hardcoded_finding(
            findings=findings,
            dedupe_keys=dedupe_keys,
            category="phone",
            field_name="",
            value=value,
            source_type=source_type,
            source_url=source_url,
            source_label=source_label,
            line=line,
            column=column,
            context=context,
            matched_by="regex.phone",
        )


def dedupe_hardcoded_findings(rows: List[dict]) -> Tuple[List[dict], int]:
    deduped: List[dict] = []
    dedupe_keys: Set[Tuple[str, str, str, str, int, int]] = set()
    skipped = 0
    for item in rows:
        category = str(item.get("category", "") or "")
        normalized = str(item.get("normalized_value", "") or "")
        source_type = str(item.get("source_type", "") or "")
        source_label = str(item.get("source_label", "") or "")
        line = int(item.get("line", 0) or 0)
        column = int(item.get("column", 0) or 0)
        key = (category, normalized, source_type, source_label, line, column)
        if not category or not normalized:
            continue
        if key in dedupe_keys:
            skipped += 1
            continue
        dedupe_keys.add(key)
        deduped.append(dict(item))
    deduped.sort(
        key=lambda finding: (
            HARD_CODED_SEVERITY_LEVELS.index(str(finding.get("severity", "low")) if str(finding.get("severity", "low")) in HARD_CODED_SEVERITY_LEVELS else "low"),
            -float(finding.get("confidence", 0.0) or 0.0),
            str(finding.get("category", "")),
            str(finding.get("source_url", "")),
            int(finding.get("line", 0) or 0),
        )
    )
    return deduped, skipped


def summarize_hardcoded_findings(findings: List[dict]) -> dict:
    by_category = {category: 0 for category in HARD_CODED_ALL_CATEGORIES}
    by_severity = {severity: 0 for severity in HARD_CODED_SEVERITY_LEVELS}
    for item in findings:
        category = str(item.get("category", "") or "")
        severity = str(item.get("severity", "") or "").lower()
        if category in by_category:
            by_category[category] += 1
        if severity in by_severity:
            by_severity[severity] += 1
    return {
        "total": len(findings),
        "by_category": by_category,
        "by_severity": by_severity,
    }


def build_hardcoded_summary_fields(findings: List[dict]) -> Dict[str, int]:
    high_or_above = 0
    pii_count = 0
    secret_count = 0
    for item in findings:
        category = str(item.get("category", "") or "")
        severity = str(item.get("severity", "") or "").lower()
        if severity in {"critical", "high"}:
            high_or_above += 1
        if category in HARD_CODED_PII_CATEGORIES:
            pii_count += 1
        if category in HARD_CODED_SECRET_CATEGORIES:
            secret_count += 1
    return {
        "hardcoded_total": len(findings),
        "hardcoded_high_or_above": high_or_above,
        "hardcoded_pii_count": pii_count,
        "hardcoded_secret_count": secret_count,
        "sensitive_total": len(findings),
        "sensitive_high_or_above": high_or_above,
        "sensitive_pii_count": pii_count,
        "sensitive_secret_count": secret_count,
    }


def resolve_sensitive_findings(result: dict) -> List[dict]:
    hardcoded_raw = result.get("hardcoded_findings")
    sensitive_raw = result.get("sensitive_findings")
    hardcoded = [item for item in hardcoded_raw if isinstance(item, dict)] if isinstance(hardcoded_raw, list) else []
    sensitive = [item for item in sensitive_raw if isinstance(item, dict)] if isinstance(sensitive_raw, list) else []
    if not hardcoded and not sensitive:
        return []
    if hardcoded and not sensitive:
        return hardcoded
    if sensitive and not hardcoded:
        return sensitive

    merged: List[dict] = []
    seen: Set[Tuple[str, str, str, str, int, int]] = set()
    for item in hardcoded + sensitive:
        category = str(item.get("category", item.get("type", "")) or "")
        normalized_value = str(item.get("normalized_value", item.get("value", "")) or "")
        source_type = str(item.get("source_type", item.get("source_kind", "")) or "")
        source_label = str(item.get("source_label", item.get("source_url", "")) or "")
        line = int(item.get("line", 0) or 0)
        column = int(item.get("column", 0) or 0)
        key = (category, normalized_value, source_type, source_label, line, column)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def summary_count(summary: dict, hardcoded_key: str, sensitive_key: str, default: int = 0) -> int:
    if hardcoded_key in summary:
        return int(summary.get(hardcoded_key, default) or 0)
    if sensitive_key in summary:
        return int(summary.get(sensitive_key, default) or 0)
    return int(default or 0)


def probe_candidate(
    url: str,
    kind: str,
    timeout: float,
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    verify_ssl: bool = True,
    proxy_url: str = "",
) -> ProbeResult:
    methods: Iterable[str] = ("GET", "POST")
    for method in methods:
        fetch_kwargs = {
            "timeout": timeout,
            "method": method,
            "headers": headers,
            "execution": execution,
            "verify_ssl": verify_ssl,
        }
        if proxy_url:
            fetch_kwargs["proxy_url"] = proxy_url
        result = fetch_text(url, **fetch_kwargs)
        if result.success:
            return ProbeResult(accessible=True, status_code=result.status_code, method=method, error=None, length=result.length)
        if result.status_code in {401, 403}:
            return ProbeResult(
                accessible=True,
                status_code=result.status_code,
                method=method,
                error="인증 또는 권한이 필요합니다.",
                length=result.length,
            )
        if result.status_code not in {405, 501, None}:
            return ProbeResult(
                accessible=False,
                status_code=result.status_code,
                method=method,
                error=result.error,
                length=result.length,
            )
    return ProbeResult(accessible=False, status_code=None, method=None, error="성공적인 프로브 응답을 받지 못했습니다.")


def build_result_row(
    candidate: Candidate,
    kind: str,
    timeout: float,
    skip_probe: bool,
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    verify_ssl: bool = True,
    proxy_url: str = "",
) -> dict:
    if skip_probe:
        probe = ProbeResult(accessible=None, status_code=None, method=None, error="프로브가 생략되었습니다.")
    else:
        probe = probe_candidate(
            candidate.url,
            kind=kind,
            timeout=timeout,
            headers=headers,
            execution=execution,
            verify_ssl=verify_ssl,
            proxy_url=proxy_url,
        )
    return {
        "path": candidate.path,
        "url": candidate.url,
        "accessible": probe.accessible,
        "status_code": probe.status_code,
        "probe_method": probe.method,
        "probe_error": probe.error,
        "length": probe.length,
        "sources": sorted(candidate.sources),
    }


def build_result_rows(
    bucket: Dict[str, Candidate],
    kind: str,
    timeout: float,
    skip_probe: bool,
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    progress: ProgressCallback = None,
    verify_ssl: bool = True,
    proxy_url: str = "",
) -> List[dict]:
    ordered_candidates = sorted(bucket.values(), key=lambda item: (item.path, item.url))
    total = len(ordered_candidates)
    kind_label = "페이지" if kind == "page" else "API"
    max_workers = max(1, execution.max_workers) if execution is not None else 1

    if skip_probe or total <= 1 or max_workers <= 1:
        rows: List[dict] = []
        for index, candidate in enumerate(ordered_candidates, start=1):
            ensure_not_cancelled(execution)
            emit_progress(progress, f"{kind_label} 후보 확인 중 {index}/{total}: {candidate.path}")
            rows.append(
                build_result_row(
                    candidate,
                    kind=kind,
                    timeout=timeout,
                    skip_probe=skip_probe,
                    headers=headers,
                    execution=execution,
                    verify_ssl=verify_ssl,
                    proxy_url=proxy_url,
                )
            )
        return rows

    indexed_rows: List[Optional[dict]] = [None] * total
    completed = 0
    worker_count = min(max_workers, total)
    executor_pool = concurrent.futures.ThreadPoolExecutor(max_workers=worker_count)
    pending_futures: Dict[concurrent.futures.Future[dict], Tuple[int, str]] = {}
    candidate_iter = iter(enumerate(ordered_candidates))

    def submit_next() -> bool:
        try:
            index, candidate = next(candidate_iter)
        except StopIteration:
            return False
        future = executor_pool.submit(
            build_result_row,
            candidate,
            kind,
            timeout,
            skip_probe,
            headers,
            execution,
            verify_ssl,
            proxy_url,
        )
        pending_futures[future] = (index, candidate.path)
        return True

    try:
        for _ in range(worker_count):
            if not submit_next():
                break

        while pending_futures:
            ensure_not_cancelled(execution)
            done, _ = concurrent.futures.wait(
                tuple(pending_futures),
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            if not done:
                continue
            for future in done:
                index, candidate_path = pending_futures.pop(future)
                indexed_rows[index] = future.result()
                completed += 1
                emit_progress(progress, f"{kind_label} 후보 확인 중 {completed}/{total}: {candidate_path}")
                submit_next()
    except Exception:
        for future in pending_futures:
            future.cancel()
        raise
    finally:
        executor_pool.shutdown(wait=True, cancel_futures=True)
    return [row for row in indexed_rows if row is not None]
def filter_candidate_bucket_by_path(
    bucket: Dict[str, Candidate],
    known_paths: Set[str],
) -> Tuple[Dict[str, Candidate], int]:
    filtered: Dict[str, Candidate] = {}
    skipped = 0
    for candidate in sorted(bucket.values(), key=lambda item: (item.path, item.url)):
        if candidate.path in known_paths:
            skipped += 1
            continue
        existing = filtered.get(candidate.path)
        if existing is not None:
            existing.sources.update(candidate.sources)
            skipped += 1
            continue
        filtered[candidate.path] = candidate
    return filtered, skipped


def dedupe_js_rows_by_url(rows: List[dict]) -> Tuple[List[dict], int]:
    deduped_by_url: Dict[str, dict] = {}
    skipped = 0
    for item in rows:
        url = str(item.get("url", "") or "")
        if not url:
            continue
        existing = deduped_by_url.get(url)
        if existing is None:
            deduped_by_url[url] = dict(item)
            continue
        skipped += 1
        existing["success"] = bool(existing.get("success")) or bool(item.get("success"))
        if existing.get("status_code") is None and item.get("status_code") is not None:
            existing["status_code"] = item.get("status_code")
        if not existing.get("error") and item.get("error"):
            existing["error"] = item.get("error")
        if not existing.get("saved_path") and item.get("saved_path"):
            existing["saved_path"] = item.get("saved_path")
        if not existing.get("save_error") and item.get("save_error"):
            existing["save_error"] = item.get("save_error")
        try:
            existing_depth = int(existing.get("depth", 0) or 0)
            item_depth = int(item.get("depth", 0) or 0)
            existing["depth"] = min(existing_depth, item_depth)
        except (TypeError, ValueError):
            pass
        try:
            existing_length = int(existing.get("length", 0) or 0)
            item_length = int(item.get("length", 0) or 0)
            existing["length"] = max(existing_length, item_length)
        except (TypeError, ValueError):
            pass
    deduped_rows = sorted(
        deduped_by_url.values(),
        key=lambda item: (int(item.get("depth", 0) or 0), str(item.get("url", ""))),
    )
    return deduped_rows, skipped


def probe_row_rank(row: dict) -> int:
    rank = 0
    accessible = row.get("accessible")
    if accessible is True:
        rank += 4
    elif accessible is False:
        rank += 2
    status_code = row.get("status_code")
    if status_code == 200:
        rank += 3
    elif isinstance(status_code, int):
        rank += 1
    if row.get("probe_method"):
        rank += 1
    return rank


def dedupe_result_rows_by_path(rows: List[dict]) -> Tuple[List[dict], int]:
    deduped_by_path: Dict[str, dict] = {}
    skipped = 0
    for item in sorted(rows, key=lambda row: (str(row.get("path", "")), str(row.get("url", "")))):
        raw_path = str(item.get("path", "") or "")
        raw_url = str(item.get("url", "") or "")
        if not raw_path and not raw_url:
            continue
        path = normalize_path(raw_path or raw_url)
        normalized = dict(item)
        normalized["path"] = path
        normalized["sources"] = sorted(set(normalized.get("sources", []) or []))
        existing = deduped_by_path.get(path)
        if existing is None:
            deduped_by_path[path] = normalized
            continue
        skipped += 1
        merged_sources = sorted(set(existing.get("sources", []) or []).union(normalized.get("sources", []) or []))
        if probe_row_rank(normalized) > probe_row_rank(existing):
            normalized["sources"] = merged_sources
            deduped_by_path[path] = normalized
            continue
        existing["sources"] = merged_sources
    deduped_rows = sorted(deduped_by_path.values(), key=lambda row: (str(row.get("path", "")), str(row.get("url", ""))))
    return deduped_rows, skipped


def apply_recursive_metadata(
    result: dict,
    config: Config,
    state: RecursiveDiscoveryState,
    failed_targets: List[dict],
    scan_records: List[dict],
) -> dict:
    enriched = dict(result)
    enriched["include_subdomains"] = config.include_subdomains
    enriched["excluded_subdomains"] = list(config.excluded_subdomains)
    enriched["proxy_url"] = config.proxy_url
    enriched["recursive_enabled"] = config.recursive_scan
    enriched["recursive_depth"] = config.recursive_depth if config.recursive_scan else 0
    enriched["recursive_scanned_targets"] = list(state.scanned_target_urls)
    enriched["recursive_discovered_targets"] = list(state.discovered_target_urls)
    enriched["recursive_total_scans"] = len(state.scanned_target_urls)
    enriched["recursive_failed_targets"] = list(failed_targets)
    enriched["recursive_dedupe"] = {
        "js": state.skipped_js_duplicates,
        "pages": state.skipped_page_duplicates,
        "apis": state.skipped_api_duplicates,
        "targets": state.skipped_target_duplicates,
    }
    enriched["recursive_scan_records"] = list(scan_records)
    return enriched


def combine_recursive_scan_results(
    config: Config,
    root_url: str,
    successful_results: List[Tuple[str, int, dict]],
    state: RecursiveDiscoveryState,
    failed_targets: List[dict],
) -> dict:
    combined_js_raw: List[dict] = []
    combined_discovered_js_urls: Set[str] = set()
    combined_pages_raw: List[dict] = []
    combined_apis_raw: List[dict] = []
    combined_hardcoded_raw: List[dict] = []
    scan_records: List[dict] = []

    for target_url, depth, result in successful_results:
        combined_js_raw.extend(result.get("js_files", []))
        combined_discovered_js_urls.update(result.get("js_discovered_urls", []))
        combined_pages_raw.extend(result.get("all_pages", []))
        combined_apis_raw.extend(result.get("all_apis", []))
        combined_hardcoded_raw.extend(result.get("hardcoded_findings", []) or [])
        scan_records.append(
            {
                "target_url": target_url,
                "depth": depth,
                "status": "success",
                "summary": result.get("summary", {}),
            }
        )

    for item in failed_targets:
        scan_records.append(
            {
                "target_url": item.get("target_url"),
                "depth": item.get("depth"),
                "status": "error",
                "error": item.get("error"),
            }
        )

    combined_js, skipped_combined_js = dedupe_js_rows_by_url(combined_js_raw)
    combined_pages, skipped_combined_pages = dedupe_result_rows_by_path(combined_pages_raw)
    combined_apis, skipped_combined_apis = dedupe_result_rows_by_path(combined_apis_raw)
    combined_hardcoded_findings, _ = dedupe_hardcoded_findings(combined_hardcoded_raw)
    combined_hardcoded_summary = summarize_hardcoded_findings(combined_hardcoded_findings)
    combined_hardcoded_summary_fields = build_hardcoded_summary_fields(combined_hardcoded_findings)
    state.skipped_js_duplicates += skipped_combined_js
    state.skipped_page_duplicates += skipped_combined_pages
    state.skipped_api_duplicates += skipped_combined_apis

    merged = {
        "input_url": root_url,
        "scanned_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "origin": get_origin_key(root_url),
        "probe_skipped": config.skip_probe,
        "include_subdomains": config.include_subdomains,
        "excluded_subdomains": list(config.excluded_subdomains),
        "max_js_files": config.max_js_files,
        "max_depth": config.max_depth,
        "max_workers": config.max_workers,
        "request_delay": config.request_delay,
        "proxy_url": config.proxy_url,
        "js_output_dir": str(normalize_js_output_dir(config.js_output_dir) or ""),
        "js_files": combined_js,
        "accessible_pages": [item for item in combined_pages if item.get("accessible") is True],
        "accessible_apis": [item for item in combined_apis if item.get("accessible") is True],
        "all_pages": combined_pages,
        "all_apis": combined_apis,
        "hardcoded_findings": combined_hardcoded_findings,
        "hardcoded_summary": combined_hardcoded_summary,
        "sensitive_findings": combined_hardcoded_findings,
        "sensitive_summary": combined_hardcoded_summary,
        "js_discovered_urls": sorted(combined_discovered_js_urls),
        "summary": {
            "js_discovered": len(combined_discovered_js_urls),
            "js_fetched": len(combined_js),
            "js_saved": sum(1 for item in combined_js if item.get("saved_path")),
            "page_count": len(combined_pages),
            "api_count": len(combined_apis),
            **combined_hardcoded_summary_fields,
        },
    }
    return apply_recursive_metadata(merged, config, state, failed_targets, scan_records)


def _discover_once(
    config: Config,
    target_url: str,
    state: RecursiveDiscoveryState,
    execution: Optional[ExecutionContext] = None,
    progress: ProgressCallback = None,
) -> dict:
    ensure_not_cancelled(execution)
    if not is_scan_target_url(target_url):
        raise ValueError("URL은 http 또는 https 형식이어야 하며 호스트가 포함되어야 합니다.")

    root_url = target_url
    root_origin = get_origin_key(root_url)
    scope = build_url_scope(
        root_url,
        include_subdomains=config.include_subdomains,
        excluded_hostnames=config.excluded_subdomains,
    )

    emit_progress(progress, f"시작 문서를 가져오는 중: {root_url}")
    html_fetch_kwargs = {
        "timeout": config.timeout,
        "method": "GET",
        "headers": config.headers,
        "execution": execution,
        "verify_ssl": config.verify_ssl,
    }
    if config.proxy_url:
        html_fetch_kwargs["proxy_url"] = config.proxy_url
    html_result = fetch_text(root_url, **html_fetch_kwargs)
    if not html_result.success:
        raise RuntimeError(f"시작 페이지를 가져오지 못했습니다: {html_result.url} / {html_result.error or html_result.status_code}")

    page_bucket: Dict[str, Candidate] = {}
    api_bucket: Dict[str, Candidate] = {}
    discovered_js_urls: Set[str] = set()
    visited_scripts: Set[str] = set()
    fetched_scripts: List[dict] = []
    hardcoded_findings: List[dict] = []
    hardcoded_dedupe_keys: Set[Tuple[str, str, str, str, int, int]] = set()
    successful_js_fetches = 0
    saved_js_files = 0
    js_output_dir = normalize_js_output_dir(config.js_output_dir)
    queue: Deque[Tuple[str, int]] = deque()

    script_urls, inline_scripts = extract_html_assets(html_result.text, root_url, scope)
    emit_progress(progress, f"연결된 스크립트 {len(script_urls)}개와 인라인 스크립트 {len(inline_scripts)}개를 찾았습니다.")
    for script_url in script_urls:
        discovered_js_urls.add(script_url)
        if script_url in state.known_js_urls:
            state.skipped_js_duplicates += 1
            continue
        queue.append((script_url, 0))

    collect_path_candidates(
        text=html_result.text,
        base_url=root_url,
        source_label=f"html:{root_url}",
        scope=scope,
        page_bucket=page_bucket,
        api_bucket=api_bucket,
    )
    collect_hardcoded_findings(
        text=html_result.text,
        source_url=root_url,
        source_label=f"html:{root_url}",
        source_type="html",
        findings=hardcoded_findings,
        dedupe_keys=hardcoded_dedupe_keys,
    )

    for inline_index, inline_script in enumerate(inline_scripts, start=1):
        inline_source_label = f"inline-script:{root_url}#{inline_index}"
        collect_path_candidates(
            text=inline_script,
            base_url=root_url,
            source_label=inline_source_label,
            scope=scope,
            page_bucket=page_bucket,
            api_bucket=api_bucket,
        )
        collect_hardcoded_findings(
            text=inline_script,
            source_url=root_url,
            source_label=inline_source_label,
            source_type="inline_script",
            findings=hardcoded_findings,
            dedupe_keys=hardcoded_dedupe_keys,
        )

    while queue and successful_js_fetches < config.max_js_files:
        ensure_not_cancelled(execution)
        script_url, depth = queue.popleft()
        if depth > config.max_depth or script_url in visited_scripts:
            continue
        if script_url in state.known_js_urls:
            state.skipped_js_duplicates += 1
            continue

        visited_scripts.add(script_url)
        emit_progress(progress, f"JS 가져오는 중 {successful_js_fetches + 1}/{config.max_js_files}: {script_url}")
        js_fetch_kwargs = {
            "timeout": config.timeout,
            "method": "GET",
            "headers": config.headers,
            "execution": execution,
            "verify_ssl": config.verify_ssl,
        }
        if config.proxy_url:
            js_fetch_kwargs["proxy_url"] = config.proxy_url
        js_result = fetch_text(script_url, **js_fetch_kwargs)
        script_record = {
            "url": script_url,
            "depth": depth,
            "status_code": js_result.status_code,
            "success": js_result.success,
            "length": js_result.length,
            "error": js_result.error,
            "saved_path": "",
            "save_error": "",
        }

        # Only mark a JS URL as globally known after a successful fetch so
        # later recursive targets can retry transient failures.
        if js_result.success:
            state.known_js_urls.add(script_url)
            successful_js_fetches += 1
            if js_output_dir is not None:
                try:
                    saved_path = save_js_file(script_url, js_result.text, js_output_dir, successful_js_fetches)
                except OSError as exc:
                    script_record["save_error"] = str(exc)
                    emit_progress(progress, f"JS 저장 실패: {script_url} / {exc}")
                else:
                    saved_js_files += 1
                    script_record["saved_path"] = str(saved_path)
                    emit_progress(progress, f"JS 저장 완료: {saved_path}")

        fetched_scripts.append(script_record)

        if not js_result.success or not js_result.text:
            continue

        collect_path_candidates(
            text=js_result.text,
            base_url=script_url,
            source_label=f"js:{script_url}",
            scope=scope,
            page_bucket=page_bucket,
            api_bucket=api_bucket,
        )
        collect_hardcoded_findings(
            text=js_result.text,
            source_url=script_url,
            source_label=f"js:{script_url}",
            source_type="js",
            findings=hardcoded_findings,
            dedupe_keys=hardcoded_dedupe_keys,
        )

        for child_url in extract_additional_js_urls(js_result.text, script_url, scope):
            discovered_js_urls.add(child_url)
            if child_url in state.known_js_urls:
                state.skipped_js_duplicates += 1
                continue
            if child_url not in visited_scripts:
                queue.append((child_url, depth + 1))

    page_bucket, skipped_pages = filter_candidate_bucket_by_path(page_bucket, state.known_page_paths)
    api_bucket, skipped_apis = filter_candidate_bucket_by_path(api_bucket, state.known_api_paths)
    state.skipped_page_duplicates += skipped_pages
    state.skipped_api_duplicates += skipped_apis

    ensure_not_cancelled(execution)
    emit_progress(progress, f"페이지 후보 {len(page_bucket)}개를 확인하는 중입니다.")
    all_pages = build_result_rows(
        bucket=page_bucket,
        kind="page",
        timeout=config.timeout,
        skip_probe=config.skip_probe,
        headers=config.headers,
        execution=execution,
        progress=progress,
        verify_ssl=config.verify_ssl,
        proxy_url=config.proxy_url,
    )

    ensure_not_cancelled(execution)
    emit_progress(progress, f"API 후보 {len(api_bucket)}개를 확인하는 중입니다.")
    all_apis = build_result_rows(
        bucket=api_bucket,
        kind="api",
        timeout=config.timeout,
        skip_probe=config.skip_probe,
        headers=config.headers,
        execution=execution,
        progress=progress,
        verify_ssl=config.verify_ssl,
        proxy_url=config.proxy_url,
    )

    all_pages, skipped_row_pages = dedupe_result_rows_by_path(all_pages)
    all_apis, skipped_row_apis = dedupe_result_rows_by_path(all_apis)
    state.skipped_page_duplicates += skipped_row_pages
    state.skipped_api_duplicates += skipped_row_apis

    for item in all_pages:
        state.known_page_paths.add(item["path"])
    for item in all_apis:
        state.known_api_paths.add(item["path"])

    hardcoded_findings, _ = dedupe_hardcoded_findings(hardcoded_findings)
    hardcoded_summary = summarize_hardcoded_findings(hardcoded_findings)
    hardcoded_summary_fields = build_hardcoded_summary_fields(hardcoded_findings)

    return {
        "input_url": root_url,
        "scanned_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "origin": root_origin,
        "probe_skipped": config.skip_probe,
        "max_js_files": config.max_js_files,
        "max_depth": config.max_depth,
        "max_workers": config.max_workers,
        "request_delay": config.request_delay,
        "proxy_url": config.proxy_url,
        "js_output_dir": str(js_output_dir or ""),
        "js_files": sorted(fetched_scripts, key=lambda item: (item["depth"], item["url"])),
        "js_discovered_urls": sorted(discovered_js_urls),
        "accessible_pages": [item for item in all_pages if item["accessible"] is True],
        "accessible_apis": [item for item in all_apis if item["accessible"] is True],
        "all_pages": all_pages,
        "all_apis": all_apis,
        "hardcoded_findings": hardcoded_findings,
        "hardcoded_summary": hardcoded_summary,
        "sensitive_findings": hardcoded_findings,
        "sensitive_summary": hardcoded_summary,
        "summary": {
            "js_discovered": len(discovered_js_urls),
            "js_fetched": len(fetched_scripts),
            "js_saved": saved_js_files,
            "page_count": len(all_pages),
            "api_count": len(all_apis),
            **hardcoded_summary_fields,
        },
    }


def discover(config: Config, progress: ProgressCallback = None, execution: Optional[ExecutionContext] = None) -> dict:
    validate_config(config)
    if not is_scan_target_url(config.url):
        raise ValueError("URL은 http 또는 https 형식이어야 하며 호스트가 포함되어야 합니다.")

    execution_context = execution or build_execution_context(config)
    state = RecursiveDiscoveryState()
    max_recursive_depth = config.recursive_depth if config.recursive_scan else 0
    recursive_scope = build_url_scope(
        config.url,
        include_subdomains=config.include_subdomains,
        excluded_hostnames=config.excluded_subdomains,
    )
    queue: Deque[Tuple[str, int]] = deque([(config.url, 0)])
    successful_results: List[Tuple[str, int, dict]] = []
    failed_targets: List[dict] = []

    while queue:
        ensure_not_cancelled(execution_context)
        target_url, depth = queue.popleft()
        if depth > max_recursive_depth:
            continue

        target_path = normalize_path(target_url)
        if target_path in state.scanned_target_paths:
            state.skipped_target_duplicates += 1
            continue

        state.scanned_target_paths.add(target_path)
        state.scanned_target_urls.append(target_url)
        emit_progress(progress, f"대상 스캔 시작 ({depth}단계): {target_url}")

        scan_progress: ProgressCallback
        if config.recursive_scan:
            scan_progress = lambda message, current=target_url, level=depth: emit_progress(progress, f"[{level}단계] {current} | {message}")
        else:
            scan_progress = progress

        try:
            result = _discover_once(config, target_url, state, execution=execution_context, progress=scan_progress)
            successful_results.append((target_url, depth, result))
            emit_progress(progress, f"대상 스캔 완료 ({depth}단계): {target_url}")
        except ScanCancelled:
            raise
        except Exception as exc:
            target_error = {"target_url": target_url, "depth": depth, "error": str(exc)}
            failed_targets.append(target_error)
            if depth == 0:
                raise
            emit_progress(progress, f"대상 스캔 실패 ({depth}단계): {target_url} / {exc}")
            continue

        if depth >= max_recursive_depth:
            continue

        for item in result.get("accessible_pages", []):
            if item.get("status_code") != 200:
                continue
            next_url = item.get("url")
            if not next_url or not url_matches_scope(next_url, recursive_scope):
                continue

            next_path = normalize_path(next_url)
            if next_path in state.scanned_target_paths or next_path in state.discovered_target_paths:
                state.skipped_target_duplicates += 1
                continue

            state.discovered_target_paths.add(next_path)
            state.discovered_target_urls.append(next_url)
            queue.append((next_url, depth + 1))
            emit_progress(progress, f"재귀 대상 발견 ({depth + 1}단계): {next_url}")

    if not successful_results:
        raise RuntimeError("스캔 결과를 생성하지 못했습니다.")

    return combine_recursive_scan_results(config, config.url, successful_results, state, failed_targets)


def discover_many(config: Config, urls: List[str], progress: ProgressCallback = None, execution: Optional[ExecutionContext] = None) -> dict:
    validate_config(config)
    execution_context = execution or build_execution_context(config)
    records: List[dict] = []
    total = len(urls)

    for index, url in enumerate(urls, start=1):
        ensure_not_cancelled(execution_context)
        emit_progress(progress, f"URL {index}/{total} 스캔 시작: {url}")
        per_url_config = Config(
            url=url,
            max_js_files=config.max_js_files,
            max_depth=config.max_depth,
            timeout=config.timeout,
            output=config.output,
            skip_probe=config.skip_probe,
            recursive_scan=config.recursive_scan,
            recursive_depth=config.recursive_depth,
            include_subdomains=config.include_subdomains,
            excluded_subdomains=tuple(config.excluded_subdomains),
            max_workers=config.max_workers,
            request_delay=config.request_delay,
            headers=dict(config.headers),
            verify_ssl=config.verify_ssl,
            proxy_url=config.proxy_url,
            js_output_dir=config.js_output_dir,
        )
        try:
            result = discover(
                per_url_config,
                progress=lambda message, current=index, count=total: emit_progress(progress, f"URL {current}/{count} {message}"),
                execution=execution_context,
            )
            records.append(decorate_scan_result(result, index, total, status="success"))
            emit_progress(progress, f"URL {index}/{total} 스캔 완료: {url}")
        except ScanCancelled:
            raise
        except Exception as exc:
            failed = build_empty_scan_result(per_url_config, url, error=str(exc), status="error")
            failed["scan_index"] = index
            failed["scan_total"] = total
            records.append(failed)
            emit_progress(progress, f"URL {index}/{total} 스캔 실패: {url} / {exc}")

    return build_batch_result(records, urls, config)


def write_json(output: Path, data: dict) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output.resolve()


def derive_export_output_paths(output: Path) -> Tuple[Path, Path]:
    suffix = output.suffix.lower()
    if suffix not in {"", ".xlsx", ".html"}:
        raise ValueError("저장 파일 이름은 확장자 없이 입력하거나 `.xlsx` / `.html` 중 하나로 입력해 주세요.")
    base = output.with_suffix("") if suffix else output
    return base.with_suffix(".xlsx"), base.with_suffix(".html")


def format_export_output_label(output_paths: Sequence[Path]) -> str:
    return ", ".join(str(path) for path in output_paths)


def save_result(output: Path, data: dict) -> Path:
    validate_output_path(output)
    suffix = output.suffix.lower()
    if suffix in {"", ".json"}:
        return write_json(output, data)
    if suffix == ".xlsx":
        return write_xlsx(output, data)
    if suffix == ".html":
        return write_html(output, data)
    raise ValueError("지원하지 않는 출력 형식입니다. `.json`, `.xlsx`, `.html`, 또는 확장자 없이 입력해 주세요.")


def write_xlsx(output: Path, data: dict) -> Path:
    sheets = build_workbook_sheets(data, output)
    if len(sheets) > 255:
        raise ValueError("Excel 시트 수 제한을 초과했습니다.")

    output.parent.mkdir(parents=True, exist_ok=True)
    _write_xlsx_package(output, sheets)
    return output.resolve()


def build_workbook_sheets(data: dict, output_path: Path) -> List[SheetSpec]:
    if "results" in data and "input_urls" in data:
        return build_batch_workbook_sheets(data, output_path)
    return build_single_workbook_sheets(data, output_path)


def save_export_bundle(output: Path, data: dict) -> Tuple[Path, Path]:
    xlsx_output, html_output = derive_export_output_paths(output)
    saved_xlsx = write_xlsx(xlsx_output, data)
    output_label = format_export_output_label((saved_xlsx, html_output.resolve()))
    saved_html = write_html(html_output, data, output_label=output_label)
    return saved_xlsx, saved_html


def build_single_workbook_sheets(result: dict, output_path: Path) -> List[SheetSpec]:
    findings = resolve_sensitive_findings(result)
    return [
        SheetSpec("요약", [[line] for line in build_summary_lines(result, output_path)]),
        SheetSpec("JS 파일", build_js_sheet_rows(result.get("js_files", []))),
        SheetSpec("페이지", build_result_sheet_rows(result.get("all_pages", []))),
        SheetSpec("API", build_result_sheet_rows(result.get("all_apis", []))),
        SheetSpec("민감정보", build_hardcoded_sheet_rows(findings)),
    ]


def build_batch_workbook_sheets(batch_result: dict, output_path: Path) -> List[SheetSpec]:
    records = list(batch_result.get("results", []))
    sheets: List[SheetSpec] = [
        SheetSpec("배치 요약", [[line] for line in build_batch_summary_lines(batch_result, output_path)]),
        SheetSpec("결과 목록", build_batch_index_sheet_rows(batch_result)),
    ]

    used_names = {sheet.name.lower() for sheet in sheets}
    if len(records) <= 253:
        for index, record in enumerate(records, start=1):
            base_name = build_record_sheet_base_name(record, index, len(records))
            sheet_name = make_unique_sheet_name(base_name, used_names)
            sheets.append(SheetSpec(sheet_name, build_record_detail_sheet_rows(record, output_path)))
        return sheets

    chunk_size = max(1, (len(records) + 252) // 253)
    for group_index, start in enumerate(range(0, len(records), chunk_size), start=1):
        group = records[start : start + chunk_size]
        base_name = f"상세 {group_index}"
        sheet_name = make_unique_sheet_name(base_name, used_names)
        sheets.append(SheetSpec(sheet_name, build_record_group_sheet_rows(group, output_path, start + 1)))
    return sheets


def build_batch_summary_lines(batch_result: dict, output_path: Path | str) -> List[str]:
    summary = batch_result["summary"]
    dedupe = summary.get("recursive_dedupe") or {}
    excluded_subdomains = ", ".join(batch_result.get("excluded_subdomains", []) or []) or "-"
    hardcoded_total = summary_count(summary, "hardcoded_total", "sensitive_total")
    hardcoded_high_or_above = summary_count(summary, "hardcoded_high_or_above", "sensitive_high_or_above")
    hardcoded_pii_count = summary_count(summary, "hardcoded_pii_count", "sensitive_pii_count")
    hardcoded_secret_count = summary_count(summary, "hardcoded_secret_count", "sensitive_secret_count")
    lines = [
        "=== 배치 요약 ===",
        f"입력 URL 개수: {summary['input_url_count']}",
        f"성공: {summary['success_count']}",
        f"실패: {summary['failed_count']}",
        f"출력 파일: {output_path}",
        f"JS 파일 합계: {summary['js_fetched']}",
        f"저장한 JS 파일 합계: {int(summary.get('js_saved', 0) or 0)}",
        f"JS 저장 폴더: {batch_result.get('js_output_dir') or '-'}",
        f"페이지 후보 합계: {summary['page_count']}",
        f"API 후보 합계: {summary['api_count']}",
        f"민감정보 탐지 합계: {hardcoded_total}",
        f"고위험 이상(High+) 합계: {hardcoded_high_or_above}",
        f"개인정보(PII) 합계: {hardcoded_pii_count}",
        f"비밀정보(Secret) 합계: {hardcoded_secret_count}",
        f"동시 요청 수: {int(batch_result.get('max_workers', 1) or 1)}",
        f"요청 딜레이(초): {float(batch_result.get('request_delay', 0.0) or 0.0):g}",
        f"프록시: {batch_result.get('proxy_url') or '-'}",
        f"서브도메인 포함: {'사용' if batch_result.get('include_subdomains', True) else '미사용'}",
        f"제외 서브도메인: {excluded_subdomains}",
        f"재귀 탐색: {'사용' if batch_result.get('recursive_enabled') else '미사용'}",
        f"재귀 단계: {int(batch_result.get('recursive_depth', 0) or 0)}",
        f"재귀 스캔 대상 합계: {int(summary.get('recursive_total_scans', 0) or 0)}",
        f"재귀 발견 대상 합계: {int(summary.get('recursive_discovered_target_count', 0) or 0)}",
        f"재귀 실패 대상 합계: {int(summary.get('recursive_failed_target_count', 0) or 0)}",
        "재귀 중복 제외(JS/페이지/API/대상) 합계: "
        f"{int(dedupe.get('js', 0) or 0)}/"
        f"{int(dedupe.get('pages', 0) or 0)}/"
        f"{int(dedupe.get('apis', 0) or 0)}/"
        f"{int(dedupe.get('targets', 0) or 0)}",
    ]
    return lines


def build_batch_index_sheet_rows(batch_result: dict) -> List[List[object]]:
    rows: List[List[object]] = [
        ["번호", "상태", "URL", "JS", "페이지", "API", "오류"],
    ]
    for record in batch_result.get("results", []):
        summary = record.get("summary") or {}
        rows.append(
            [
                record.get("scan_index", ""),
                record.get("status", ""),
                record.get("input_url", ""),
                summary.get("js_fetched", 0),
                summary.get("page_count", 0),
                summary.get("api_count", 0),
                record.get("error", "") or "",
            ]
        )
    return rows


def build_record_sheet_base_name(record: dict, index: int, total: int) -> str:
    url = str(record.get("input_url", f"URL {index}"))
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc or f"URL{index}"
    path_part = parsed.path.strip("/").replace("/", "_")
    pieces = [f"{index:0{len(str(total))}d}", host]
    if path_part:
        pieces.append(path_part)
    if record.get("status") and record.get("status") != "success":
        pieces.append("오류")
    return "_".join(part for part in pieces if part)


def build_record_detail_sheet_rows(record: dict, output_path: Path | str) -> List[List[object]]:
    findings = resolve_sensitive_findings(record)
    rows: List[List[object]] = [[line] for line in build_summary_lines(record, output_path)]
    rows.extend([[]])
    rows.append(["=== JS 파일 ==="])
    rows.extend(build_js_sheet_rows(record.get("js_files", [])))
    rows.extend([[]])
    rows.append(["=== 페이지 ==="])
    rows.extend(build_result_sheet_rows(record.get("all_pages", [])))
    rows.extend([[]])
    rows.append(["=== API ==="])
    rows.extend(build_result_sheet_rows(record.get("all_apis", [])))
    rows.extend([[]])
    rows.append(["=== 민감정보 ==="])
    rows.extend(build_hardcoded_sheet_rows(findings))
    return rows


def build_record_group_sheet_rows(records: List[dict], output_path: Path | str, start_index: int) -> List[List[object]]:
    rows: List[List[object]] = []
    for offset, record in enumerate(records, start=0):
        if rows:
            rows.append([])
        sheet_title = f"=== {start_index + offset}번 결과 ==="
        rows.append([sheet_title])
        rows.extend([[line] for line in build_summary_lines(record, output_path)])
        rows.append([])
        rows.append(["=== JS 파일 ==="])
        rows.extend(build_js_sheet_rows(record.get("js_files", [])))
        rows.append([])
        rows.append(["=== 페이지 ==="])
        rows.extend(build_result_sheet_rows(record.get("all_pages", [])))
        rows.append([])
        rows.append(["=== API ==="])
        rows.extend(build_result_sheet_rows(record.get("all_apis", [])))
        rows.append([])
        rows.append(["=== 민감정보 ==="])
        rows.extend(build_hardcoded_sheet_rows(resolve_sensitive_findings(record)))
    return rows


def build_js_sheet_rows(js_files: List[dict]) -> List[List[object]]:
    rows: List[List[object]] = [["깊이", "상태", "성공", "길이", "저장 경로", "저장 오류", "오류", "URL"]]
    for item in js_files:
        rows.append(
            [
                item.get("depth", ""),
                item.get("status_code", "-"),
                "예" if item.get("success") else "아니오",
                item.get("length", ""),
                item.get("saved_path", "") or "",
                item.get("save_error", "") or "",
                item.get("error", "") or "",
                item.get("url", ""),
            ]
        )
    return rows


def build_result_sheet_rows(rows_data: List[dict]) -> List[List[object]]:
    rows: List[List[object]] = [["상태", "접근 가능", "방법", "경로", "출처", "URL"]]
    for item in rows_data:
        rows.append(
            [
                item.get("status_code", "-"),
                format_accessible_label(item.get("accessible")),
                item.get("probe_method", "") or "",
                item.get("path", "") or "",
                ", ".join(item.get("sources", [])),
                item.get("url", ""),
            ]
        )
    return rows


def build_hardcoded_sheet_rows(rows_data: List[dict]) -> List[List[object]]:
    rows: List[List[object]] = [
        [
            "심각도",
            "신뢰도",
            "범주",
            "필드",
            "값",
            "원본 유형",
            "라인",
            "열",
            "출처",
            "URL",
            "탐지 방식",
            "컨텍스트",
        ]
    ]
    for item in rows_data:
        rows.append(
            [
                item.get("severity", ""),
                item.get("confidence", ""),
                item.get("category", ""),
                item.get("field_name", ""),
                item.get("value", item.get("masked_value", "")),
                item.get("source_type", ""),
                item.get("line", ""),
                item.get("column", ""),
                item.get("source_label", ""),
                item.get("source_url", ""),
                item.get("matched_by", ""),
                item.get("context", ""),
            ]
        )
    return rows


def _normalize_language(language: Optional[str]) -> str:
    return "en" if str(language or "").strip().lower() == "en" else "ko"


def _localized_text(language: str, korean: str, english: str) -> str:
    return english if _normalize_language(language) == "en" else korean


def _format_yes_no_label(value: bool, language: str) -> str:
    return _localized_text(language, "예" if value else "아니오", "Yes" if value else "No")


def _format_enabled_label(value: bool, language: str) -> str:
    return _localized_text(language, "사용" if value else "미사용", "Enabled" if value else "Disabled")


def _format_status_label(value: object, language: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "success":
        return _localized_text(language, "성공", "Success")
    if normalized == "error":
        return _localized_text(language, "실패", "Failed")
    if normalized == "unknown":
        return _localized_text(language, "알 수 없음", "Unknown")
    return str(value or "")


def format_accessible_label(value: Optional[bool], language: str = "ko") -> str:
    if value is True:
        return _localized_text(language, "예", "Yes")
    if value is False:
        return _localized_text(language, "아니오", "No")
    return _localized_text(language, "생략", "Skipped")


def sanitize_sheet_name(value: str) -> str:
    cleaned = re.sub(r"[\x00-\x1F\[\]\*:/?\\]", "_", value).strip().strip("'")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Sheet"


def make_unique_sheet_name(value: str, used_names: Set[str]) -> str:
    base = sanitize_sheet_name(value)[:31]
    if not base:
        base = "Sheet"

    candidate = base
    counter = 2
    while candidate.lower() in used_names:
        suffix = f"_{counter}"
        candidate = f"{base[:31 - len(suffix)]}{suffix}"
        counter += 1

    used_names.add(candidate.lower())
    return candidate


def excel_column_name(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _xlsx_is_section_row(row: Sequence[object]) -> bool:
    return len(row) == 1 and str(row[0] or "").strip().startswith("===")


def _xlsx_is_header_row(rows: List[List[object]], row_index: int) -> bool:
    row = rows[row_index - 1]
    if not row or len(row) <= 1:
        return False
    if row_index == 1:
        return True
    previous = rows[row_index - 2]
    return _xlsx_is_section_row(previous)


def _xlsx_style_id_for_row(rows: List[List[object]], row_index: int) -> int:
    row = rows[row_index - 1]
    if not row:
        return 0
    if _xlsx_is_section_row(row):
        return 1 if row_index == 1 else 3
    if _xlsx_is_header_row(rows, row_index):
        return 2
    if len(row) == 1:
        return 4
    return 5


def _xlsx_row_height(rows: List[List[object]], row_index: int) -> Optional[int]:
    row = rows[row_index - 1]
    if not row:
        return None
    if _xlsx_is_section_row(row):
        return 26 if row_index == 1 else 22
    if _xlsx_is_header_row(rows, row_index):
        return 22
    if len(row) == 1:
        return 20
    return None


def _xlsx_merge_ranges(rows: List[List[object]]) -> List[str]:
    max_columns = max((len(row) for row in rows), default=1)
    if max_columns <= 1:
        return []
    last_column = excel_column_name(max_columns)
    return [f"A{row_index}:{last_column}{row_index}" for row_index, row in enumerate(rows, start=1) if len(row) == 1 and row]


def _xlsx_column_widths(rows: List[List[object]]) -> List[int]:
    max_columns = max((len(row) for row in rows), default=1)
    widths = [14] * max_columns
    for row in rows:
        for index, value in enumerate(row):
            text = str(value or "")
            estimated = min(max(len(text) + 3, 12), 48)
            if "\n" in text:
                estimated = min(max(max(len(part) for part in text.splitlines()) + 3, 16), 52)
            widths[index] = max(widths[index], estimated)
    if max_columns == 1:
        widths[0] = max(widths[0], 72)
    return widths


def xlsx_cell_xml(cell_ref: str, value: object, style_id: int = 0) -> str:
    if value is None:
        return ""
    style_attr = f' s="{style_id}"' if style_id else ""

    if isinstance(value, bool):
        return f'<c r="{cell_ref}" t="b"{style_attr}><v>{1 if value else 0}</v></c>'

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{cell_ref}"{style_attr}><v>{value}</v></c>'

    text = xml_escape(str(value), {"'": "&apos;", '"': "&quot;"})
    return f'<c r="{cell_ref}" t="inlineStr"{style_attr}><is><t xml:space="preserve">{text}</t></is></c>'


def xlsx_sheet_xml(rows: List[List[object]]) -> str:
    column_widths = _xlsx_column_widths(rows)
    column_xml = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(column_widths, start=1)
    )
    merge_ranges = _xlsx_merge_ranges(rows)
    row_xml_parts: List[str] = []
    for row_index, row in enumerate(rows, start=1):
        style_id = _xlsx_style_id_for_row(rows, row_index)
        height = _xlsx_row_height(rows, row_index)
        row_attrs = [f'r="{row_index}"']
        if height is not None:
            row_attrs.append(f'ht="{height}"')
            row_attrs.append('customHeight="1"')
        if not row:
            row_xml_parts.append(f'<row {" ".join(row_attrs)}/>')
            continue

        cell_xml_parts: List[str] = []
        for column_index, value in enumerate(row, start=1):
            cell_xml = xlsx_cell_xml(f"{excel_column_name(column_index)}{row_index}", value, style_id=style_id)
            if cell_xml:
                cell_xml_parts.append(cell_xml)

        if cell_xml_parts:
            row_xml_parts.append(f'<row {" ".join(row_attrs)}>{"".join(cell_xml_parts)}</row>')
        else:
            row_xml_parts.append(f'<row {" ".join(row_attrs)}/>')

    merge_xml = ""
    if merge_ranges:
        merge_cells_body = "".join(f'<mergeCell ref="{ref}"/>' for ref in merge_ranges)
        merge_xml = f'<mergeCells count="{len(merge_ranges)}">{merge_cells_body}</mergeCells>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        f"<cols>{column_xml}</cols>"
        f'<sheetData>{"".join(row_xml_parts)}</sheetData>'
        f"{merge_xml}"
        '<pageMargins left="0.4" right="0.4" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>'
        "</worksheet>"
    )


def xlsx_attr(value: str) -> str:
    return xml_escape(value, {"'": "&apos;", '"': "&quot;"})


def xlsx_workbook_xml(sheet_names: List[str]) -> str:
    sheets_xml = "".join(
        f'<sheet name="{xlsx_attr(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets_xml}</sheets>"
        "</workbook>"
    )


def xlsx_workbook_rels_xml(sheet_count: int) -> str:
    rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for index in range(1, sheet_count + 1):
        rels.append(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{sheet_count + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    rels.append("</Relationships>")
    return "".join(rels)


def xlsx_root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def xlsx_content_types_xml(sheet_count: int) -> str:
    overrides = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for index in range(1, sheet_count + 1):
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    overrides.append("</Types>")
    return "".join(overrides)


def xlsx_styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="4">'
        '<font><sz val="11"/><color rgb="FF0F172A"/><name val="Calibri"/><family val="2"/></font>'
        '<font><b/><sz val="14"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/><family val="2"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/><family val="2"/></font>'
        '<font><b/><sz val="11"/><color rgb="FF1E3A5F"/><name val="Segoe UI"/><family val="2"/></font>'
        '</fonts>'
        '<fills count="6">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF0F4C81"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF2563EB"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFE0ECFF"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFF8FAFC"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="2">'
        '<border><left/><right/><top/><bottom/><diagonal/></border>'
        '<border><left style="thin"><color rgb="FFD8E1EC"/></left><right style="thin"><color rgb="FFD8E1EC"/></right><top style="thin"><color rgb="FFD8E1EC"/></top><bottom style="thin"><color rgb="FFD8E1EC"/></bottom><diagonal/></border>'
        '</borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="6">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"><alignment vertical="top" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="3" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="left" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment horizontal="left" vertical="top" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"><alignment horizontal="left" vertical="top" wrapText="1"/></xf>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )


def _write_xlsx_package(output: Path, sheets: List[SheetSpec]) -> None:
    sheet_names = [sheet.name for sheet in sheets]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", xlsx_content_types_xml(len(sheets)))
        archive.writestr("_rels/.rels", xlsx_root_rels_xml())
        archive.writestr("xl/workbook.xml", xlsx_workbook_xml(sheet_names))
        archive.writestr("xl/_rels/workbook.xml.rels", xlsx_workbook_rels_xml(len(sheets)))
        archive.writestr("xl/styles.xml", xlsx_styles_xml())
        for index, sheet in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", xlsx_sheet_xml(sheet.rows))


def filter_table_rows(
    rows: Sequence[Tuple[object, ...]],
    columns: Sequence[str],
    filter_column: Optional[str],
    filter_text: str,
) -> List[Tuple[object, ...]]:
    keyword = filter_text.strip().casefold()
    if not keyword:
        return list(rows)

    if not filter_column:
        target_indexes = list(range(len(columns)))
    else:
        try:
            target_indexes = [columns.index(filter_column)]
        except ValueError:
            return list(rows)

    filtered_rows: List[Tuple[object, ...]] = []
    for row in rows:
        for index in target_indexes:
            if index >= len(row):
                continue
            if keyword in str(row[index]).casefold():
                filtered_rows.append(row)
                break
    return filtered_rows


def build_summary_lines(result: dict, output_path: Path | str, language: str = "ko") -> List[str]:
    language = _normalize_language(language)
    summary = result["summary"]
    findings = resolve_sensitive_findings(result)
    hardcoded_total = summary_count(summary, "hardcoded_total", "sensitive_total", default=len(findings))
    hardcoded_high_or_above = summary_count(summary, "hardcoded_high_or_above", "sensitive_high_or_above")
    hardcoded_pii_count = summary_count(summary, "hardcoded_pii_count", "sensitive_pii_count")
    hardcoded_secret_count = summary_count(summary, "hardcoded_secret_count", "sensitive_secret_count")
    excluded_subdomains = ", ".join(result.get("excluded_subdomains", []) or []) or "-"
    lines = [
        _localized_text(language, "=== 요약 ===", "=== Summary ==="),
        f"{_localized_text(language, '입력 URL', 'Input URL')}: {result['input_url']}",
        f"{_localized_text(language, '스캔 시각', 'Scanned at')}: {result['scanned_at']}",
        f"{_localized_text(language, '출력 파일', 'Output file')}: {output_path}",
    ]
    if result.get("scan_index") is not None and result.get("scan_total") is not None:
        lines.append(f"{_localized_text(language, '선택 위치', 'Selection')}: {result['scan_index']}/{result['scan_total']}")
    if result.get("status"):
        lines.append(f"{_localized_text(language, '상태', 'Status')}: {_format_status_label(result['status'], language)}")
    if result.get("error"):
        lines.append(f"{_localized_text(language, '오류', 'Error')}: {result['error']}")
    lines.extend(
        [
            f"{_localized_text(language, '가져온 JS 파일 수', 'Fetched JS files')}: {summary['js_fetched']}",
            f"{_localized_text(language, '저장한 JS 파일 수', 'Saved JS files')}: {int(summary.get('js_saved', 0) or 0)}",
            f"{_localized_text(language, 'JS 저장 폴더', 'JS output directory')}: {result.get('js_output_dir') or '-'}",
            f"{_localized_text(language, '페이지 후보 수', 'Page candidates')}: {summary['page_count']}",
            f"{_localized_text(language, 'API 후보 수', 'API candidates')}: {summary['api_count']}",
            f"{_localized_text(language, '민감정보 탐지 수', 'Hardcoded findings')}: {hardcoded_total}",
            f"{_localized_text(language, '고위험 이상(High+) 수', 'High or above findings')}: {hardcoded_high_or_above}",
            f"{_localized_text(language, '개인정보(PII) 탐지 수', 'PII findings')}: {hardcoded_pii_count}",
            f"{_localized_text(language, '비밀정보(Secret) 탐지 수', 'Secret findings')}: {hardcoded_secret_count}",
            f"{_localized_text(language, '동시 요청 수', 'Max workers')}: {int(result.get('max_workers', 1) or 1)}",
            f"{_localized_text(language, '요청 딜레이(초)', 'Request delay (sec)')}: {float(result.get('request_delay', 0.0) or 0.0):g}",
            f"{_localized_text(language, '프록시', 'Proxy')}: {result.get('proxy_url') or '-'}",
            f"{_localized_text(language, '프로브 생략 여부', 'Probe skipped')}: {_format_yes_no_label(bool(result['probe_skipped']), language)}",
            f"{_localized_text(language, '서브도메인 포함', 'Include subdomains')}: {_format_enabled_label(bool(result.get('include_subdomains', True)), language)}",
            f"{_localized_text(language, '제외 서브도메인', 'Excluded subdomains')}: {excluded_subdomains}",
            f"{_localized_text(language, '재귀 탐색', 'Recursive scan')}: {_format_enabled_label(bool(result.get('recursive_enabled')), language)}",
            f"{_localized_text(language, '재귀 단계', 'Recursive depth')}: {int(result.get('recursive_depth', 0) or 0)}",
            f"{_localized_text(language, '재귀 스캔 대상 수', 'Recursive scanned targets')}: {int(result.get('recursive_total_scans', 1) or 1)}",
            f"{_localized_text(language, '재귀 발견 대상 수', 'Recursive discovered targets')}: {len(result.get('recursive_discovered_targets', []) or [])}",
            f"{_localized_text(language, '재귀 실패 대상 수', 'Recursive failed targets')}: {len(result.get('recursive_failed_targets', []) or [])}",
        ]
    )
    dedupe = result.get("recursive_dedupe") or {}
    lines.append(
        f"{_localized_text(language, '재귀 중복 제외(JS/페이지/API/대상): ', 'Recursive dedupe removed (JS/Page/API/Target): ')}"
        f"{int(dedupe.get('js', 0) or 0)}/"
        f"{int(dedupe.get('pages', 0) or 0)}/"
        f"{int(dedupe.get('apis', 0) or 0)}/"
        f"{int(dedupe.get('targets', 0) or 0)}"
    )
    if result["accessible_pages"]:
        lines.append("")
        lines.append(_localized_text(language, "접근 가능한 페이지:", "Accessible pages:"))
        for item in result["accessible_pages"][:10]:
            lines.append(f"[{item['status_code']}] {item['path']} -> {item['url']}")
        if len(result["accessible_pages"]) > 10:
            remaining = len(result["accessible_pages"]) - 10
            lines.append(_localized_text(language, f"... 외 {remaining}개", f"... and {remaining} more"))
    if result["accessible_apis"]:
        lines.append("")
        lines.append(_localized_text(language, "접근 가능한 API:", "Accessible APIs:"))
        for item in result["accessible_apis"][:10]:
            lines.append(f"[{item['status_code']}] {item['path']} -> {item['url']}")
        if len(result["accessible_apis"]) > 10:
            remaining = len(result["accessible_apis"]) - 10
            lines.append(_localized_text(language, f"... 외 {remaining}개", f"... and {remaining} more"))
    return lines


def build_summary_text(result: dict, output_path: Path | str, language: str = "ko") -> str:
    return "\n".join(build_summary_lines(result, output_path, language=language))


def build_batch_summary_text(batch_result: dict, selected_result: dict, output_path: Path | str, language: str = "ko") -> str:
    language = _normalize_language(language)
    lines = [
        _localized_text(language, "=== 배치 요약 ===", "=== Batch Summary ==="),
        f"{_localized_text(language, '입력 URL 개수', 'Input URLs')}: {len(batch_result.get('input_urls', []))}",
        f"{_localized_text(language, '성공', 'Success')}: {batch_result.get('success_count', 0)}",
        f"{_localized_text(language, '실패', 'Failed')}: {batch_result.get('failed_count', 0)}",
        f"{_localized_text(language, '출력 파일', 'Output file')}: {output_path}",
    ]
    lines.append("")
    lines.extend(build_summary_lines(selected_result, output_path, language=language))
    return "\n".join(lines)


def print_summary(result: dict, output_path: Path) -> None:
    print()
    print(build_summary_text(result, output_path))

    if result["accessible_pages"]:
        print()
        print("=== 접근 가능한 페이지 ===")
        for item in result["accessible_pages"]:
            print(f"[{item['status_code']}] {item['path']} -> {item['url']}")

    if result["accessible_apis"]:
        print()
        print("=== 접근 가능한 API ===")
        for item in result["accessible_apis"]:
            print(f"[{item['status_code']}] {item['path']} -> {item['url']}")


def _build_html_summary_list(lines: Sequence[str]) -> str:
    items = [line for line in lines if str(line).strip()]
    return "<ul>" + "".join(f"<li>{html_escape(str(line))}</li>" for line in items) + "</ul>"


def _build_html_summary_blocks(lines: Sequence[str]) -> str:
    pairs: List[Tuple[str, str]] = []
    notes: List[str] = []
    for raw_line in lines:
        line = str(raw_line or "").strip()
        if not line or line.startswith("==="):
            continue
        if ": " in line:
            label, value = line.split(": ", 1)
            pairs.append((label, value))
        else:
            notes.append(line)
    details = "".join(
        f'<div class="summary-item"><dt>{html_escape(label)}</dt><dd>{html_escape(value)}</dd></div>'
        for label, value in pairs
    )
    note_html = ""
    if notes:
        note_html = '<div class="summary-notes">' + "".join(f"<p>{html_escape(note)}</p>" for note in notes) + "</div>"
    return f'<div class="summary-grid">{details}</div>{note_html}'


def _build_html_metric_cards(metrics: Sequence[Tuple[str, object]]) -> str:
    return (
        '<div class="metric-grid">'
        + "".join(
            f'<article class="metric-card"><span class="metric-label">{html_escape(str(label))}</span>'
            f'<strong class="metric-value">{html_escape(str(value))}</strong></article>'
            for label, value in metrics
        )
        + "</div>"
    )


def _html_status_tone(status: object) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == "success":
        return "success"
    if normalized == "error":
        return "error"
    return "neutral"


def _build_html_status_badge(status: object) -> str:
    normalized = str(status or "").strip().lower()
    label = _format_status_label(normalized or status, "en") if normalized else "Unknown"
    return f'<span class="status-badge {html_escape(_html_status_tone(normalized))}">{html_escape(label)}</span>'


def _build_result_metric_cards(result: dict) -> str:
    summary = result.get("summary") or {}
    findings = resolve_sensitive_findings(result)
    metrics = [
        ("JS Files", summary.get("js_fetched", 0)),
        ("Pages", summary.get("page_count", 0)),
        ("APIs", summary.get("api_count", 0)),
        ("Sensitive", summary_count(summary, "hardcoded_total", "sensitive_total", default=len(findings))),
        ("High+", summary_count(summary, "hardcoded_high_or_above", "sensitive_high_or_above")),
        ("Recursive", int(result.get("recursive_total_scans", 1) or 1)),
    ]
    return _build_html_metric_cards(metrics)


def _build_batch_metric_cards(batch_result: dict) -> str:
    summary = batch_result.get("summary") or {}
    metrics = [
        ("Input URLs", summary.get("input_url_count", len(batch_result.get("input_urls", [])))),
        ("Success", summary.get("success_count", batch_result.get("success_count", 0))),
        ("Failed", summary.get("failed_count", batch_result.get("failed_count", 0))),
        ("JS Files", summary.get("js_fetched", 0)),
        ("Pages", summary.get("page_count", 0)),
        ("APIs", summary.get("api_count", 0)),
    ]
    return _build_html_metric_cards(metrics)


def _build_html_table(rows: Sequence[Sequence[object]]) -> str:
    if not rows:
        return "<p>No data</p>"
    header = rows[0]
    body = rows[1:]
    thead = "".join(f"<th>{html_escape(str(cell))}</th>" for cell in header)
    body_rows = []
    for row in body:
        cells = "".join(f"<td>{html_escape(str(cell))}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    tbody = "".join(body_rows) if body_rows else "<tr><td colspan=\"100%\">-</td></tr>"
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>'


def _build_html_empty_state(message: str) -> str:
    return f'<div class="empty-state">{html_escape(message)}</div>'


def _slugify_html_anchor(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or "section"


def _build_html_quick_nav(items: Sequence[Tuple[str, str]]) -> str:
    links = "".join(
        f'<a class="quick-nav-link" href="#{html_escape(anchor)}">{html_escape(label)}</a>'
        for label, anchor in items
        if label and anchor
    )
    return f'<nav class="quick-nav panel">{links}</nav>' if links else ""


def _build_html_file_pills(output_label: Path | str) -> str:
    values = [part.strip() for part in str(output_label or "").split(",") if part.strip()]
    if not values:
        values = [str(output_label or "-")]
    return '<div class="file-pill-row">' + "".join(
        f'<span class="file-pill">{html_escape(value)}</span>' for value in values
    ) + "</div>"


def _build_html_resource_preview(title: str, rows: Sequence[dict], empty_message: str) -> str:
    if not rows:
        return (
            '<article class="panel inset-panel preview-panel">'
            f"<h3>{html_escape(title)}</h3>"
            f"{_build_html_empty_state(empty_message)}"
            "</article>"
        )
    items: List[str] = []
    for item in rows[:6]:
        status = item.get("status_code", "-")
        path = item.get("path", "") or "/"
        url = item.get("url", "") or ""
        method = item.get("probe_method", "") or ""
        subtitle = f"{method} {url}".strip()
        items.append(
            '<li class="resource-item">'
            f'<span class="resource-status">{html_escape(str(status))}</span>'
            '<div class="resource-copy">'
            f'<strong>{html_escape(str(path))}</strong>'
            f'<span>{html_escape(subtitle)}</span>'
            "</div>"
            "</li>"
        )
    return (
        '<article class="panel inset-panel preview-panel">'
        f"<h3>{html_escape(title)}</h3>"
        f'<ul class="resource-list">{"".join(items)}</ul>'
        "</article>"
    )


def _build_html_sensitive_preview(findings: Sequence[dict]) -> str:
    if not findings:
        return (
            '<article class="panel inset-panel preview-panel">'
            "<h3>Sensitive Highlights</h3>"
            f"{_build_html_empty_state('No sensitive findings were detected.')}"
            "</article>"
        )
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ranked = sorted(
        findings,
        key=lambda item: (
            severity_rank.get(str(item.get("severity", "")).lower(), 0),
            float(item.get("confidence", 0.0) or 0.0),
        ),
        reverse=True,
    )
    items: List[str] = []
    for item in ranked[:5]:
        severity_key = str(item.get("severity", "unknown") or "unknown").lower()
        severity = severity_key.upper()
        category = item.get("category") or item.get("type") or "unknown"
        value = item.get("masked_value") or item.get("value") or "-"
        source = item.get("source_url") or item.get("source_label") or "-"
        items.append(
            '<li class="finding-item">'
            f'<span class="severity-pill severity-{html_escape(severity_key)}">{html_escape(severity)}</span>'
            '<div class="finding-copy">'
            f'<strong>{html_escape(str(category))}</strong>'
            f'<span>{html_escape(str(value))}</span>'
            f'<code>{html_escape(str(source))}</code>'
            "</div>"
            "</li>"
        )
    return (
        '<article class="panel inset-panel preview-panel">'
        "<h3>Sensitive Highlights</h3>"
        f'<ul class="finding-list">{"".join(items)}</ul>'
        "</article>"
    )


def _build_html_detail_block(title: str, body: str, anchor_id: str, note: str = "", *, open_by_default: bool = False) -> str:
    open_attr = " open" if open_by_default else ""
    note_html = f'<span class="detail-note">{html_escape(note)}</span>' if note else ""
    return (
        f'<details class="detail-accordion" id="{html_escape(anchor_id)}"{open_attr}>'
        "<summary>"
        f'<span class="detail-title">{html_escape(title)}</span>'
        f"{note_html}"
        "</summary>"
        f'<div class="detail-body">{body}</div>'
        "</details>"
    )


def _build_html_result_jump_cards(batch_result: dict) -> str:
    cards: List[str] = []
    for index, record in enumerate(batch_result.get("results", []), start=1):
        summary = record.get("summary") or {}
        cards.append(
            f'<a class="result-jump-card" href="#result-{index}">'
            '<div class="result-jump-head">'
            f'<span class="result-jump-index">Result {index}</span>'
            f"{_build_html_status_badge(record.get('status', 'unknown'))}"
            "</div>"
            f'<strong class="result-jump-url">{html_escape(str(record.get("input_url") or f"Result {index}"))}</strong>'
            '<div class="result-jump-metrics">'
            f'<span>JS {html_escape(str(summary.get("js_fetched", 0)))}</span>'
            f'<span>Pages {html_escape(str(summary.get("page_count", 0)))}</span>'
            f'<span>APIs {html_escape(str(summary.get("api_count", 0)))}</span>'
            "</div>"
            "</a>"
        )
    if not cards:
        return _build_html_empty_state("No result records are available.")
    return '<div class="result-jump-grid">' + "".join(cards) + "</div>"


def _build_single_html_section(result: dict, output_label: Path | str, *, include_title: bool = False, index: int = 0) -> str:
    anchor_base = f"result-{index}" if include_title else "overview"
    title_text = result.get("input_url") or (f"Result {index}" if include_title else "Scan Result")
    section_title = (
        '<div class="section-heading">'
        "<div>"
        f'<p class="section-kicker">{"Selected Result" if include_title else "Overview"}</p>'
        f'<h2>{html_escape(str(title_text))}</h2>'
        "</div>"
        f"{_build_html_status_badge(result.get('status', 'unknown'))}"
        "</div>"
    )
    findings = resolve_sensitive_findings(result)
    summary_lines = build_summary_lines(result, output_label, language="en")
    accessible_pages = result.get("accessible_pages", [])
    accessible_apis = result.get("accessible_apis", [])
    detail_body = (
        '<div class="detail-grid">'
        '<div class="panel inset-panel">'
        "<h3>JS Files</h3>"
        f"{_build_html_table(build_js_sheet_rows(result.get('js_files', [])))}"
        "</div>"
        '<div class="panel inset-panel">'
        "<h3>Pages</h3>"
        f"{_build_html_table(build_result_sheet_rows(result.get('all_pages', [])))}"
        "</div>"
        '<div class="panel inset-panel">'
        "<h3>APIs</h3>"
        f"{_build_html_table(build_result_sheet_rows(result.get('all_apis', [])))}"
        "</div>"
        '<div class="panel inset-panel">'
        "<h3>Sensitive Findings</h3>"
        f"{_build_html_table(build_hardcoded_sheet_rows(findings))}"
        "</div>"
        "</div>"
    )
    return (
        f'<section class="panel result-section" id="{html_escape(anchor_base)}">'
        f"{section_title}"
        f"{_build_result_metric_cards(result)}"
        '<div class="content-grid summary-layout">'
        '<div class="panel inset-panel">'
        "<h3>Summary</h3>"
        f"{_build_html_summary_blocks(summary_lines)}"
        "</div>"
        '<div class="panel inset-panel">'
        "<h3>Exported Files</h3>"
        f"{_build_html_file_pills(output_label)}"
        '<p class="supporting-copy">Saving this report writes both the Excel workbook and this HTML file together.</p>'
        "</div>"
        "</div>"
        '<div class="preview-grid">'
        f"{_build_html_resource_preview('Accessible Pages', accessible_pages, 'No accessible pages were confirmed.')}"
        f"{_build_html_resource_preview('Accessible APIs', accessible_apis, 'No accessible APIs were confirmed.')}"
        f"{_build_html_sensitive_preview(findings)}"
        "</div>"
        f"{_build_html_detail_block('Detailed Tables', detail_body, f'{anchor_base}-details', note='JS / Pages / APIs / Sensitive', open_by_default=not include_title)}"
        "</section>"
    )


def build_html_report(data: dict, output_label: Path | str) -> str:
    title = "Route API Discovery Report"
    nav_items: List[Tuple[str, str]] = [("Overview", "overview")]
    if "results" in data and "input_urls" in data:
        summary_html = _build_html_summary_blocks(build_batch_summary_lines(data, output_label))
        index_html = _build_html_table(build_batch_index_sheet_rows(data))
        sections = "".join(
            _build_single_html_section(record, output_label, include_title=True, index=index)
            for index, record in enumerate(data.get("results", []), start=1)
        )
        nav_items.append(("Results", "results"))
        nav_items.extend((f"Result {index}", f"result-{index}") for index, _ in enumerate(data.get("results", []), start=1))
        body = (
            '<section class="panel hero-panel" id="overview">'
            '<div class="hero-copy">'
            f"<p class=\"eyebrow\">Designed Export</p><h1>{html_escape(title)}</h1>"
            '<p class="hero-text">A bundled export for review: scan summary first, readable highlights second, full raw tables last.</p>'
            f"{_build_html_file_pills(output_label)}"
            "</div>"
            f"{_build_batch_metric_cards(data)}"
            "</section>"
            f"{_build_html_quick_nav(nav_items)}"
            '<section class="panel" id="results">'
            "<h2>Batch Summary</h2>"
            f"{summary_html}"
            '<div class="section-heading"><h3>Results At A Glance</h3>'
            f"{_build_html_status_badge('success' if not data.get('failed_count', 0) else 'unknown')}"
            "</div>"
            f"{_build_html_result_jump_cards(data)}"
            f"{_build_html_detail_block('Batch Result Table', index_html, 'batch-table', note='Status / URL / JS / Pages / APIs')}"
            f"</section>{sections}"
        )
    else:
        nav_items.extend([("Pages / APIs / Sensitive", "overview-details")])
        body = (
            '<section class="panel hero-panel" id="overview">'
            '<div class="hero-copy">'
            f"<p class=\"eyebrow\">Designed Export</p><h1>{html_escape(title)}</h1>"
            '<p class="hero-text">A bundled export for review: scan summary first, readable highlights second, full raw tables last.</p>'
            f"{_build_html_file_pills(output_label)}"
            "</div>"
            f"{_build_result_metric_cards(data)}"
            "</section>"
            f"{_build_html_quick_nav(nav_items)}"
            f"{_build_single_html_section(data, output_label)}"
        )
    return (
        "<!DOCTYPE html>"
        "<html lang=\"en\">"
        "<head>"
        "<meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html_escape(title)}</title>"
        "<style>"
        ":root{color-scheme:light;--bg:#eef4fb;--panel:#ffffff;--border:#d8e1ec;--text:#0f172a;--muted:#475569;--blue:#2563eb;--navy:#0f4c81;--soft:#f8fbff;--success:#166534;--success-bg:#dcfce7;--error:#991b1b;--error-bg:#fee2e2;--neutral:#1e3a5f;--neutral-bg:#dbeafe;--amber:#b45309;--amber-bg:#fef3c7;}"
        "*{box-sizing:border-box;}"
        "body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:radial-gradient(circle at top left,#dbeafe 0,#eef4fb 32%,#f8fbff 100%);color:var(--text);line-height:1.55;}"
        ".report-shell{max-width:1360px;margin:0 auto;padding:32px 20px 56px;}"
        ".panel{background:rgba(255,255,255,.92);backdrop-filter:blur(6px);border:1px solid rgba(216,225,236,.95);border-radius:22px;padding:22px;box-shadow:0 16px 40px rgba(15,23,42,.08);margin:0 0 18px;}"
        ".hero-panel{background:linear-gradient(135deg,#0f4c81 0%,#2563eb 58%,#7dd3fc 100%);color:#fff;overflow:hidden;}"
        ".hero-copy{margin-bottom:18px;}"
        ".eyebrow{margin:0 0 8px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;opacity:.82;}"
        "h1,h2,h3{margin:0 0 12px;line-height:1.15;}"
        "h1{font-size:34px;}"
        "h2{font-size:24px;}"
        "h3{font-size:16px;color:#143b63;}"
        ".hero-text{margin:0;max-width:860px;color:rgba(255,255,255,.92);}"
        ".quick-nav{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:10px;padding:14px 18px;background:rgba(255,255,255,.86);backdrop-filter:blur(14px);}"
        ".quick-nav-link{display:inline-flex;align-items:center;padding:8px 12px;border-radius:999px;background:var(--soft);border:1px solid var(--border);color:var(--navy);text-decoration:none;font-weight:700;font-size:13px;}"
        ".quick-nav-link:hover{background:#dbeafe;}"
        ".file-pill-row{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;}"
        ".file-pill{display:inline-flex;max-width:100%;padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);font-size:13px;font-weight:700;word-break:break-all;}"
        ".metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:14px;}"
        ".metric-card{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);border-radius:18px;padding:14px 16px;min-height:92px;display:flex;flex-direction:column;justify-content:space-between;}"
        ".metric-label{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.78);}"
        ".metric-value{font-size:28px;font-weight:800;color:#fff;}"
        ".result-section .metric-grid .metric-card{background:var(--soft);border-color:var(--border);box-shadow:none;}"
        ".result-section .metric-label{color:var(--muted);}"
        ".result-section .metric-value{color:var(--navy);}"
        ".content-grid{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin:14px 0;}"
        ".summary-layout{align-items:start;}"
        ".preview-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:0 0 14px;}"
        ".inset-panel{background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);padding:18px;border-radius:18px;box-shadow:none;margin-bottom:14px;}"
        ".preview-panel{height:100%;}"
        ".section-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px;}"
        ".section-kicker{margin:0 0 6px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}"
        ".summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 14px;}"
        ".summary-item{padding:12px 14px;border:1px solid var(--border);border-radius:14px;background:#fff;}"
        ".summary-item dt{margin:0 0 6px;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);}"
        ".summary-item dd{margin:0;font-size:14px;font-weight:600;color:var(--text);word-break:break-word;}"
        ".summary-notes p{margin:10px 0 0;padding:12px 14px;border-left:4px solid var(--blue);background:#fff;border-radius:12px;color:var(--muted);}"
        ".supporting-copy{margin:14px 0 0;color:var(--muted);font-size:13px;}"
        ".status-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:7px 12px;font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;}"
        ".status-badge.success{background:var(--success-bg);color:var(--success);}"
        ".status-badge.error{background:var(--error-bg);color:var(--error);}"
        ".status-badge.neutral{background:var(--neutral-bg);color:var(--neutral);}"
        ".empty-state{padding:18px;border:1px dashed var(--border);border-radius:16px;background:#fff;color:var(--muted);font-size:14px;}"
        ".resource-list,.finding-list{list-style:none;margin:0;padding:0;display:grid;gap:10px;}"
        ".resource-item,.finding-item{display:flex;gap:12px;padding:12px;border:1px solid var(--border);border-radius:16px;background:#fff;align-items:flex-start;}"
        ".resource-status{display:inline-flex;min-width:48px;justify-content:center;padding:6px 8px;border-radius:999px;background:var(--neutral-bg);color:var(--neutral);font-weight:800;font-size:12px;}"
        ".resource-copy,.finding-copy{display:grid;gap:4px;min-width:0;}"
        ".resource-copy strong,.finding-copy strong{font-size:14px;color:var(--text);word-break:break-word;}"
        ".resource-copy span,.finding-copy span{font-size:13px;color:var(--muted);word-break:break-word;}"
        ".finding-copy code{font-family:'Cascadia Code','Consolas',monospace;font-size:12px;color:var(--navy);word-break:break-all;background:#eff6ff;border-radius:10px;padding:6px 8px;}"
        ".severity-pill{display:inline-flex;align-items:center;padding:6px 8px;border-radius:999px;font-size:11px;font-weight:800;letter-spacing:.08em;}"
        ".severity-pill.severity-critical,.severity-pill.severity-high{background:var(--error-bg);color:var(--error);}"
        ".severity-pill.severity-medium{background:var(--amber-bg);color:var(--amber);}"
        ".severity-pill.severity-low,.severity-pill.severity-unknown{background:var(--neutral-bg);color:var(--neutral);}"
        ".detail-accordion{border:1px solid var(--border);border-radius:18px;background:#fff;overflow:hidden;margin-top:14px;}"
        ".detail-accordion summary{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 18px;cursor:pointer;font-weight:800;color:var(--navy);background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);list-style:none;}"
        ".detail-accordion summary::-webkit-details-marker{display:none;}"
        ".detail-note{font-size:12px;font-weight:700;color:var(--muted);}"
        ".detail-body{padding:18px;}"
        ".detail-grid{display:grid;grid-template-columns:1fr;gap:14px;}"
        ".result-jump-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:14px;}"
        ".result-jump-card{display:grid;gap:10px;padding:16px;border-radius:18px;border:1px solid var(--border);background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);text-decoration:none;color:inherit;box-shadow:0 10px 24px rgba(15,23,42,.05);}"
        ".result-jump-card:hover{transform:translateY(-1px);box-shadow:0 14px 28px rgba(15,23,42,.08);}"
        ".result-jump-head{display:flex;align-items:center;justify-content:space-between;gap:10px;}"
        ".result-jump-index{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);}"
        ".result-jump-url{font-size:15px;color:var(--text);word-break:break-word;}"
        ".result-jump-metrics{display:flex;flex-wrap:wrap;gap:8px;font-size:12px;color:var(--navy);font-weight:700;}"
        ".table-wrap{overflow:auto;border:1px solid var(--border);border-radius:16px;background:#fff;}"
        "table{width:100%;border-collapse:separate;border-spacing:0;min-width:760px;}"
        "th,td{padding:11px 12px;vertical-align:top;text-align:left;font-size:13px;border-bottom:1px solid var(--border);word-break:break-word;}"
        "th{position:sticky;top:0;background:linear-gradient(180deg,#eff6ff 0%,#e0ecff 100%);color:#143b63;font-weight:800;z-index:1;}"
        "tbody tr:nth-child(even) td{background:#fbfdff;}"
        "tbody tr:hover td{background:#eef6ff;}"
        "ul{margin:0;padding-left:20px;}"
        "@media (max-width:1100px){.preview-grid{grid-template-columns:1fr;}}"
        "@media (max-width:960px){.content-grid{grid-template-columns:1fr;}.report-shell{padding:20px 14px 40px;}h1{font-size:28px;}.panel{padding:18px;}.quick-nav{top:0;padding:12px;}}"
        "</style>"
        "</head>"
        "<body>"
        '<main class="report-shell">'
        f"{body}"
        "</main>"
        "</body>"
        "</html>"
    )


def write_html(output: Path, data: dict, output_label: Optional[Path | str] = None) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_html_report(data, output_label or output)
    output.write_text(report, encoding="utf-8")
    return output.resolve()


def gui_main(
    initial_url: Optional[str] = None,
    initial_output: Optional[str] = None,
    initial_js_output_dir: Optional[str] = None,
) -> int:
    try:
        sys.modules.setdefault("route_api_discovery", sys.modules[__name__])
        from route_api_discovery_qt import run_qt_gui
    except ImportError as exc:
        print(f"PySide6 GUI를 사용할 수 없습니다: {exc}", file=sys.stderr)
        return 1

    return run_qt_gui(
        initial_url=initial_url,
        initial_output=initial_output,
        initial_js_output_dir=initial_js_output_dir,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args: Optional[argparse.Namespace] = None
    try:
        args = parse_args(argv)
        if args.gui:
            return gui_main(
                initial_url=args.url,
                initial_output=str(args.output),
                initial_js_output_dir=str(args.save_js_dir) if args.save_js_dir else None,
            )
        config = build_config(args)
        if not config.verify_ssl:
            print("경고: SSL 인증서 검증이 비활성화되었습니다. 신뢰할 수 있는 대상에만 사용해 주세요.", file=sys.stderr)
        result = discover(config)
        output_path = save_result(config.output, result)
        print_summary(result, output_path)
        return 0
    except KeyboardInterrupt:
        print("사용자에 의해 중단되었습니다.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        if args is not None and getattr(args, "debug", False):
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
