"""Directory brute-forcing module for discovering hidden paths."""

import os
import requests
from pathlib import Path
from typing import List, Set, Dict, Any
from urllib.parse import urljoin, urlparse
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DirectoryBruteForcer:
    """
    웹 애플리케이션의 숨겨진 디렉토리와 경로를 브루트포스로 발견합니다.

    Features:
    - Wordlist 기반 경로 탐색
    - HTTP 응답 코드 분석 (200, 301, 302, 401, 403)
    - 발견된 경로 자동 수집
    - 커스텀 헤더 및 타임아웃 설정
    """

    # HTTP 상태 코드: 경로가 존재함을 나타내는 코드들
    VALID_STATUS_CODES = [200, 301, 302, 401, 403]

    def __init__(self, base_url: str, wordlist_path: str = None, timeout: int = 10):
        """
        Initialize DirectoryBruteForcer.

        Args:
            base_url: 대상 웹 애플리케이션의 기본 URL
            wordlist_path: 브루트포싱에 사용할 wordlist 파일 경로
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.discovered_paths: List[Dict[str, Any]] = []
        self.discovered_urls: Set[str] = set()  # URL 중복 체크용

        # 기본 wordlist 경로 설정
        if wordlist_path is None:
            project_root = Path(__file__).parent.parent.parent
            wordlist_path = project_root / 'wordlists' / 'common_directories.txt'

        self.wordlist_path = Path(wordlist_path)

        # Session 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def load_wordlist(self) -> List[str]:
        """
        Wordlist 파일에서 경로 목록을 로드합니다.

        Returns:
            경로 문자열 리스트
        """
        if not self.wordlist_path.exists():
            print(f"[!] Wordlist 파일을 찾을 수 없습니다: {self.wordlist_path}")
            return []

        paths = []
        with open(self.wordlist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 빈 줄과 주석 제외
                if line and not line.startswith('#'):
                    # '/'로 시작하지 않으면 추가
                    if not line.startswith('/'):
                        line = '/' + line
                    paths.append(line)

        print(f"[*] Wordlist 로드 완료: {len(paths)}개 경로")
        return paths

    def test_path(self, path: str) -> Dict[str, Any]:
        """
        특정 경로가 존재하는지 테스트합니다.

        Args:
            path: 테스트할 경로 (예: /admin, /api/v1)

        Returns:
            발견된 경로 정보 딕셔너리 또는 None
        """
        url = urljoin(self.base_url, path)

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                verify=False,
                allow_redirects=False  # 리다이렉트 자체도 유효한 발견
            )

            if response.status_code in self.VALID_STATUS_CODES:
                content_length = len(response.content) if response.content else 0
                content_type = response.headers.get('Content-Type', 'unknown')
                
                print(f"[+] 경로 발견: {path} (Status: {response.status_code})")
                
                return {
                    'path': url,
                    'status_code': response.status_code,
                    'content_length': content_length,
                    'content_type': content_type
                }

        except requests.exceptions.Timeout:
            print(f"[!] 타임아웃: {path}")
        except requests.exceptions.RequestException as e:
            # 연결 실패는 조용히 처리 (404 등)
            pass

        return None

    def brute_force(self, max_paths: int = None) -> List[Dict[str, Any]]:
        """
        Wordlist를 사용하여 디렉토리 브루트포싱을 수행합니다.

        Args:
            max_paths: 최대 테스트할 경로 수 (None이면 전체)

        Returns:
            발견된 경로 정보 리스트
        """
        paths = self.load_wordlist()

        if not paths:
            print("[!] 테스트할 경로가 없습니다.")
            return []

        if max_paths:
            paths = paths[:max_paths]

        print(f"[*] 디렉토리 브루트포싱 시작: {self.base_url}")
        print(f"[*] 테스트할 경로: {len(paths)}개")

        for i, path in enumerate(paths, 1):
            path_info = self.test_path(path)
            if path_info:
                # URL 중복 체크
                if path_info['path'] not in self.discovered_urls:
                    self.discovered_urls.add(path_info['path'])
                    self.discovered_paths.append(path_info)

            # 진행 상황 표시 (10개마다)
            if i % 10 == 0:
                print(f"[*] 진행: {i}/{len(paths)} ({len(self.discovered_paths)}개 발견)")

        print(f"[+] 브루트포싱 완료: 총 {len(self.discovered_paths)}개 경로 발견")
        return self.discovered_paths

    def get_discovered_paths(self) -> List[Dict[str, Any]]:
        """
        발견된 모든 경로를 반환합니다.

        Returns:
            발견된 경로 정보 리스트
        """
        return self.discovered_paths


def main():
    """테스트용 메인 함수"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python directory_bruteforcer.py <target_url>")
        sys.exit(1)

    target_url = sys.argv[1]
    bruteforcer = DirectoryBruteForcer(target_url)

    discovered = bruteforcer.brute_force()

    print("\n" + "="*60)
    print(f"발견된 경로 ({len(discovered)}개):")
    print("="*60)
    for path in discovered:
        print(f"  {path}")


if __name__ == '__main__':
    main()
