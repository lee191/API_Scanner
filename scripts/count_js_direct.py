#!/usr/bin/env python3
"""직접 JavaScript 파일을 읽어서 API 엔드포인트 카운팅"""

import re
from pathlib import Path
from typing import Set

def extract_api_calls(js_file: Path) -> Set[str]:
    """JavaScript 파일에서 API 호출 추출"""
    content = js_file.read_text(encoding='utf-8', errors='ignore')

    api_calls = set()

    # fetch() 패턴
    fetch_pattern = r'fetch\s*\(\s*[`\'"](.*?)[`\'"]'
    for match in re.finditer(fetch_pattern, content):
        url = match.group(1)
        if '/api/' in url or '/internal/' in url:
            api_calls.add(url)

    # fetch with template literal
    fetch_template = r'fetch\s*\(\s*`([^`]+)`'
    for match in re.finditer(fetch_template, content):
        url = match.group(1)
        if '/api/' in url or '/internal/' in url:
            api_calls.add(url)

    # axios 패턴
    axios_pattern = r'axios\.(get|post|put|delete|patch)\s*\(\s*[`\'"](.*?)[`\'"]'
    for match in re.finditer(axios_pattern, content):
        url = match.group(2)
        if '/api/' in url or '/internal/' in url:
            api_calls.add(url)

    # 직접 URL 문자열
    direct_url = r'[`\'"](/(?:api|internal)/[^`\'"]+)[`\'"]'
    for match in re.finditer(direct_url, content):
        url = match.group(1)
        api_calls.add(url)

    return api_calls

def main():
    js_dir = Path('../test-app/static')

    all_endpoints = set()
    file_counts = {}

    print("=" * 80)
    print("JavaScript 파일 직접 분석")
    print("=" * 80)
    print()

    js_files = sorted(js_dir.glob('*.js'))

    for js_file in js_files:
        endpoints = extract_api_calls(js_file)
        file_counts[js_file.name] = len(endpoints)
        all_endpoints.update(endpoints)

        if endpoints:
            print(f"{js_file.name}: {len(endpoints)}개")
            for ep in sorted(endpoints)[:5]:  # 처음 5개만 표시
                print(f"  - {ep}")
            if len(endpoints) > 5:
                print(f"  ... 외 {len(endpoints) - 5}개 더")
            print()

    print("=" * 80)
    print(f"총 고유 API 엔드포인트: {len(all_endpoints)}개")
    print("=" * 80)
    print()

    # 정규화된 버전으로 다시 카운트
    normalized = set()
    for url in all_endpoints:
        # Base URL 변수 제거 (앞에 있는 것들)
        url_norm = re.sub(r'^\$\{[^}]*[Uu]rl[^}]*\}/?', '', url)
        url_norm = re.sub(r'^\$\{[^}]*[Bb]ase[^}]*\}/?', '', url_norm)
        url_norm = re.sub(r'^\$\{API_BASE\}/?', '', url_norm)
        url_norm = re.sub(r'^\$\{HOST\}/?', '', url_norm)

        # 파라미터 정규화
        url_norm = re.sub(r'\$\{[^}]+\}', ':param', url_norm)
        url_norm = re.sub(r'\{[^}]+\}', ':param', url_norm)
        url_norm = re.sub(r'/\d+', '/:param', url_norm)
        url_norm = url_norm.split('?')[0]
        url_norm = url_norm.lower().rstrip('/')

        # :param으로 시작하는 경우 (base URL 변수가 남은 경우) 제거
        url_norm = re.sub(r'^:param/?', '/', url_norm)

        # URL이 /로 시작하지 않으면 추가
        if url_norm and not url_norm.startswith('/'):
            url_norm = '/' + url_norm

        # 연속된 :param 수정
        url_norm = re.sub(r':param:param', ':param/:param', url_norm)

        # 유효한 URL만 추가 (최소 2개 이상의 경로 세그먼트 필요)
        if url_norm and url_norm != '/':
            parts = [p for p in url_norm.split('/') if p and p != ':param']
            if len(parts) >= 2:  # /api/users 형식 (최소 2개)
                normalized.add(url_norm)

    print(f"정규화 후 고유 엔드포인트: {len(normalized)}개")
    print()

    # 엔드포인트 목록 출력
    print("전체 목록 (정규화):")
    for i, ep in enumerate(sorted(normalized), 1):
        print(f"{i:2}. {ep}")

if __name__ == '__main__':
    main()
