#!/usr/bin/env python3
"""Route discovery utility for pages and API endpoints."""

from __future__ import annotations

import argparse
import concurrent.futures
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
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape as xml_escape


USER_AGENT = "RouteApiDiscovery/1.0"
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
}
SUPPORTED_OUTPUT_SUFFIXES = {"", ".json", ".xlsx"}
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
    parser.add_argument("--output", type=Path, default=Path("discovery-result.json"), help="결과 파일 경로(.json/.xlsx 또는 확장자 없음, 기본값: discovery-result.json)")
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
    validate_output_path(config.output)


def validate_output_path(output: Path) -> None:
    suffix = output.suffix.lower()
    if suffix not in SUPPORTED_OUTPUT_SUFFIXES:
        raise ValueError("지원하지 않는 출력 형식입니다. `.json`, `.xlsx`, 또는 확장자 없이 입력해 주세요.")


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
        if not is_http_url(url):
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
        "summary": {
            "js_discovered": 0,
            "js_fetched": 0,
            "page_count": 0,
            "api_count": 0,
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
        "page_count": 0,
        "api_count": 0,
    }
    for record in records:
        summary = record.get("summary") or {}
        totals["js_discovered"] += int(summary.get("js_discovered", 0) or 0)
        totals["js_fetched"] += int(summary.get("js_fetched", 0) or 0)
        totals["page_count"] += int(summary.get("page_count", 0) or 0)
        totals["api_count"] += int(summary.get("api_count", 0) or 0)

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


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    hostname = parsed.hostname or ""
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not _is_disallowed_host(hostname)


def resolve_absolute_url(base_url: str, candidate: str) -> Optional[str]:
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
    if not is_http_url(absolute):
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


def fetch_text(
    url: str,
    timeout: float,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    verify_ssl: bool = True,
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

    try:
        if execution is not None:
            execution.request_throttle.wait_for_turn(cancel_event=execution.cancel_event)
            ensure_not_cancelled(execution)
        with urlopen(request, timeout=timeout, context=ssl_context) as response:
            text = read_response_text(response)
            return FetchResult(
                url=url,
                status_code=response.getcode(),
                text=text,
                success=True,
                length=len(text),
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
    for match in QUOTED_PATH_RE.finditer(text):
        raw_value = match.group("value").strip()
        absolute = resolve_absolute_url(base_url, raw_value)
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
            absolute = resolve_absolute_url(base_url, raw_value)
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
    for script_src in parser.script_srcs:
        absolute = resolve_absolute_url(page_url, script_src)
        # Anything declared in <script src> should be treated as a JS fetch
        # target, even when the URL itself omits a .js suffix.
        if absolute and url_matches_scope(absolute, scope):
            script_urls.append(absolute)
    return script_urls, parser.inline_scripts


def extract_additional_js_urls(script_text: str, source_url: str, scope: UrlScope) -> List[str]:
    discovered: List[str] = []
    for pattern in JS_IMPORT_RE_LIST:
        for match in pattern.finditer(script_text):
            raw_value = match.group("value").strip()
            absolute = resolve_absolute_url(source_url, raw_value)
            if absolute and url_matches_scope(absolute, scope) and should_follow_js(absolute):
                discovered.append(absolute)
    return discovered


def probe_candidate(
    url: str,
    kind: str,
    timeout: float,
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    verify_ssl: bool = True,
) -> ProbeResult:
    methods: Iterable[str] = ("HEAD", "OPTIONS", "GET") if kind == "api" else ("HEAD", "GET")
    for method in methods:
        result = fetch_text(url, timeout=timeout, method=method, headers=headers, execution=execution, verify_ssl=verify_ssl)
        if result.success:
            return ProbeResult(accessible=True, status_code=result.status_code, method=method, error=None)
        if result.status_code in {401, 403}:
            return ProbeResult(
                accessible=True,
                status_code=result.status_code,
                method=method,
                error="인증 또는 권한이 필요합니다.",
            )
        if result.status_code not in {405, 501, None}:
            return ProbeResult(accessible=False, status_code=result.status_code, method=method, error=result.error)
    return ProbeResult(accessible=False, status_code=None, method=None, error="성공적인 프로브 응답을 받지 못했습니다.")


def build_result_row(
    candidate: Candidate,
    kind: str,
    timeout: float,
    skip_probe: bool,
    headers: Optional[Dict[str, str]] = None,
    execution: Optional[ExecutionContext] = None,
    verify_ssl: bool = True,
) -> dict:
    if skip_probe:
        probe = ProbeResult(accessible=None, status_code=None, method=None, error="프로브가 생략되었습니다.")
    else:
        probe = probe_candidate(candidate.url, kind=kind, timeout=timeout, headers=headers, execution=execution, verify_ssl=verify_ssl)
    return {
        "path": candidate.path,
        "url": candidate.url,
        "accessible": probe.accessible,
        "status_code": probe.status_code,
        "probe_method": probe.method,
        "probe_error": probe.error,
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
    scan_records: List[dict] = []

    for target_url, depth, result in successful_results:
        combined_js_raw.extend(result.get("js_files", []))
        combined_discovered_js_urls.update(result.get("js_discovered_urls", []))
        combined_pages_raw.extend(result.get("all_pages", []))
        combined_apis_raw.extend(result.get("all_apis", []))
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
        "js_files": combined_js,
        "accessible_pages": [item for item in combined_pages if item.get("accessible") is True],
        "accessible_apis": [item for item in combined_apis if item.get("accessible") is True],
        "all_pages": combined_pages,
        "all_apis": combined_apis,
        "js_discovered_urls": sorted(combined_discovered_js_urls),
        "summary": {
            "js_discovered": len(combined_discovered_js_urls),
            "js_fetched": len(combined_js),
            "page_count": len(combined_pages),
            "api_count": len(combined_apis),
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
    if not is_http_url(target_url):
        raise ValueError("URL은 http 또는 https 형식이어야 하며 호스트가 포함되어야 합니다.")

    root_url = target_url
    root_origin = get_origin_key(root_url)
    scope = build_url_scope(
        root_url,
        include_subdomains=config.include_subdomains,
        excluded_hostnames=config.excluded_subdomains,
    )

    emit_progress(progress, f"시작 문서를 가져오는 중: {root_url}")
    html_result = fetch_text(root_url, timeout=config.timeout, method="GET", headers=config.headers, execution=execution, verify_ssl=config.verify_ssl)
    if not html_result.success:
        raise RuntimeError(f"시작 페이지를 가져오지 못했습니다: {html_result.url} / {html_result.error or html_result.status_code}")

    page_bucket: Dict[str, Candidate] = {}
    api_bucket: Dict[str, Candidate] = {}
    discovered_js_urls: Set[str] = set()
    visited_scripts: Set[str] = set()
    fetched_scripts: List[dict] = []
    successful_js_fetches = 0
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

    for inline_script in inline_scripts:
        collect_path_candidates(
            text=inline_script,
            base_url=root_url,
            source_label=f"inline-script:{root_url}",
            scope=scope,
            page_bucket=page_bucket,
            api_bucket=api_bucket,
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
        js_result = fetch_text(script_url, timeout=config.timeout, method="GET", headers=config.headers, execution=execution, verify_ssl=config.verify_ssl)
        fetched_scripts.append(
            {
                "url": script_url,
                "depth": depth,
                "status_code": js_result.status_code,
                "success": js_result.success,
                "length": js_result.length,
                "error": js_result.error,
            }
        )

        # Only mark a JS URL as globally known after a successful fetch so
        # later recursive targets can retry transient failures.
        if js_result.success:
            state.known_js_urls.add(script_url)
            successful_js_fetches += 1

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
    )

    all_pages, skipped_row_pages = dedupe_result_rows_by_path(all_pages)
    all_apis, skipped_row_apis = dedupe_result_rows_by_path(all_apis)
    state.skipped_page_duplicates += skipped_row_pages
    state.skipped_api_duplicates += skipped_row_apis

    for item in all_pages:
        state.known_page_paths.add(item["path"])
    for item in all_apis:
        state.known_api_paths.add(item["path"])

    return {
        "input_url": root_url,
        "scanned_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "origin": root_origin,
        "probe_skipped": config.skip_probe,
        "max_js_files": config.max_js_files,
        "max_depth": config.max_depth,
        "max_workers": config.max_workers,
        "request_delay": config.request_delay,
        "js_files": sorted(fetched_scripts, key=lambda item: (item["depth"], item["url"])),
        "js_discovered_urls": sorted(discovered_js_urls),
        "accessible_pages": [item for item in all_pages if item["accessible"] is True],
        "accessible_apis": [item for item in all_apis if item["accessible"] is True],
        "all_pages": all_pages,
        "all_apis": all_apis,
        "summary": {
            "js_discovered": len(discovered_js_urls),
            "js_fetched": len(fetched_scripts),
            "page_count": len(all_pages),
            "api_count": len(all_apis),
        },
    }


def discover(config: Config, progress: ProgressCallback = None, execution: Optional[ExecutionContext] = None) -> dict:
    validate_config(config)
    if not is_http_url(config.url):
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
        )
        try:
            result = discover(
                per_url_config,
                progress=lambda message, current=index, count=total: emit_progress(progress, f"URL {current}/{count} {message}"),
                execution=execution_context,
            )
            records.append(decorate_scan_result(result, index, total, status="success"))
            emit_progress(progress, f"URL {index}/{total} 스캔 완료: {url}")
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


def save_result(output: Path, data: dict) -> Path:
    validate_output_path(output)
    suffix = output.suffix.lower()
    if suffix in {"", ".json"}:
        return write_json(output, data)
    if suffix == ".xlsx":
        return write_xlsx(output, data)
    raise ValueError("지원하지 않는 출력 형식입니다. `.json`, `.xlsx`, 또는 확장자 없이 입력해 주세요.")


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


def build_single_workbook_sheets(result: dict, output_path: Path) -> List[SheetSpec]:
    return [
        SheetSpec("요약", [[line] for line in build_summary_lines(result, output_path)]),
        SheetSpec("JS 파일", build_js_sheet_rows(result.get("js_files", []))),
        SheetSpec("페이지", build_result_sheet_rows(result.get("all_pages", []))),
        SheetSpec("API", build_result_sheet_rows(result.get("all_apis", []))),
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


def build_batch_summary_lines(batch_result: dict, output_path: Path) -> List[str]:
    summary = batch_result["summary"]
    dedupe = summary.get("recursive_dedupe") or {}
    excluded_subdomains = ", ".join(batch_result.get("excluded_subdomains", []) or []) or "-"
    lines = [
        "=== 배치 요약 ===",
        f"입력 URL 개수: {summary['input_url_count']}",
        f"성공: {summary['success_count']}",
        f"실패: {summary['failed_count']}",
        f"출력 파일: {output_path}",
        f"JS 파일 합계: {summary['js_fetched']}",
        f"페이지 후보 합계: {summary['page_count']}",
        f"API 후보 합계: {summary['api_count']}",
        f"동시 요청 수: {int(batch_result.get('max_workers', 1) or 1)}",
        f"요청 딜레이(초): {float(batch_result.get('request_delay', 0.0) or 0.0):g}",
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


def build_record_detail_sheet_rows(record: dict, output_path: Path) -> List[List[object]]:
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
    return rows


def build_record_group_sheet_rows(records: List[dict], output_path: Path, start_index: int) -> List[List[object]]:
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
    return rows


def build_js_sheet_rows(js_files: List[dict]) -> List[List[object]]:
    rows: List[List[object]] = [["깊이", "상태", "성공", "길이", "오류", "URL"]]
    for item in js_files:
        rows.append(
            [
                item.get("depth", ""),
                item.get("status_code", "-"),
                "예" if item.get("success") else "아니오",
                item.get("length", ""),
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


def xlsx_cell_xml(cell_ref: str, value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, bool):
        return f'<c r="{cell_ref}" t="b"><v>{1 if value else 0}</v></c>'

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{cell_ref}"><v>{value}</v></c>'

    text = xml_escape(str(value), {"'": "&apos;", '"': "&quot;"})
    return f'<c r="{cell_ref}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'


def xlsx_sheet_xml(rows: List[List[object]]) -> str:
    row_xml_parts: List[str] = []
    for row_index, row in enumerate(rows, start=1):
        if not row:
            row_xml_parts.append(f'<row r="{row_index}"/>')
            continue

        cell_xml_parts: List[str] = []
        for column_index, value in enumerate(row, start=1):
            cell_xml = xlsx_cell_xml(f"{excel_column_name(column_index)}{row_index}", value)
            if cell_xml:
                cell_xml_parts.append(cell_xml)

        if cell_xml_parts:
            row_xml_parts.append(f'<row r="{row_index}">{"".join(cell_xml_parts)}</row>')
        else:
            row_xml_parts.append(f'<row r="{row_index}"/>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheetData>{"".join(row_xml_parts)}</sheetData>'
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
        '<fonts count="1"><font><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
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


def build_summary_lines(result: dict, output_path: Path, language: str = "ko") -> List[str]:
    language = _normalize_language(language)
    summary = result["summary"]
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
            f"{_localized_text(language, '페이지 후보 수', 'Page candidates')}: {summary['page_count']}",
            f"{_localized_text(language, 'API 후보 수', 'API candidates')}: {summary['api_count']}",
            f"{_localized_text(language, '동시 요청 수', 'Max workers')}: {int(result.get('max_workers', 1) or 1)}",
            f"{_localized_text(language, '요청 딜레이(초)', 'Request delay (sec)')}: {float(result.get('request_delay', 0.0) or 0.0):g}",
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


def build_summary_text(result: dict, output_path: Path, language: str = "ko") -> str:
    return "\n".join(build_summary_lines(result, output_path, language=language))


def build_batch_summary_text(batch_result: dict, selected_result: dict, output_path: Path, language: str = "ko") -> str:
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

    if not result["accessible_pages"] and not result["accessible_apis"]:
        print()
        print("접근 가능한 페이지나 API를 찾지 못했거나, 프로브를 생략했습니다.")
        print("전체 목록은 결과 파일에서 확인해 주세요.")


def gui_main(initial_url: Optional[str] = None, initial_output: Optional[str] = None) -> int:
    try:
        sys.modules.setdefault("route_api_discovery", sys.modules[__name__])
        from route_api_discovery_qt import run_qt_gui
    except ImportError as exc:
        print(f"PySide6 GUI를 사용할 수 없습니다: {exc}", file=sys.stderr)
        return 1

    return run_qt_gui(initial_url=initial_url, initial_output=initial_output)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args: Optional[argparse.Namespace] = None
    try:
        args = parse_args(argv)
        if args.gui:
            return gui_main(initial_url=args.url, initial_output=str(args.output))
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
