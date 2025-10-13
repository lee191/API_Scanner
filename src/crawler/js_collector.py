"""JavaScript 파일 자동 수집 모듈."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List, Set
import re
import time


class JSCollector:
    """웹사이트에서 JavaScript 파일을 자동으로 수집하는 클래스."""

    def __init__(self, base_url: str, timeout: int = 10):
        """
        Args:
            base_url: 대상 웹사이트 URL
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.js_urls: Set[str] = set()
        self.js_contents: dict = {}

    def collect_from_page(self, url: str = None) -> List[str]:
        """
        페이지에서 JavaScript 파일 URL을 수집합니다.

        Args:
            url: 수집할 페이지 URL (기본값: base_url)

        Returns:
            수집된 JavaScript 파일 URL 리스트
        """
        if url is None:
            url = self.base_url

        try:
            print(f"[*] 페이지 크롤링: {url}")
            response = self.session.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()
            print(f"[+] 페이지 로드 성공 (상태 코드: {response.status_code})")

            soup = BeautifulSoup(response.text, 'html.parser')

            # <script src="..."> 태그에서 외부 JS 파일 수집
            script_tags = soup.find_all('script', src=True)
            print(f"[*] <script> 태그 발견: {len(script_tags)}개")

            for script in script_tags:
                js_url = urljoin(url, script['src'])
                print(f"[*] JS URL 발견: {js_url}")

                # 같은 도메인의 JS 파일만 수집
                if self._is_same_domain(js_url):
                    self.js_urls.add(js_url)
                    print(f"[+] 수집 대상 추가: {js_url}")
                else:
                    print(f"[-] 다른 도메인 (건너뜀): {js_url}")

            # JSP, ASP, PHP 등 서버 사이드 스크립트도 수집
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.endswith(ext) for ext in ['.jsp', '.asp', '.aspx', '.php']):
                    full_url = urljoin(url, href)
                    if self._is_same_domain(full_url):
                        self.js_urls.add(full_url)
                        print(f"[+] 서버 스크립트 발견: {full_url}")

            # 인라인 스크립트에서 동적으로 로드되는 JS 파일 찾기
            for script in soup.find_all('script', src=False):
                if script.string:
                    # fetch(), axios, $.getScript 등에서 JS 파일 URL 추출
                    js_patterns = [
                        r'["\']([^"\']+\.js)["\']',
                        r'src:\s*["\']([^"\']+\.js)["\']',
                    ]
                    for pattern in js_patterns:
                        matches = re.findall(pattern, script.string)
                        for match in matches:
                            js_url = urljoin(url, match)
                            if self._is_same_domain(js_url):
                                self.js_urls.add(js_url)

            print(f"[+] 발견된 JS 파일: {len(self.js_urls)}개")
            return list(self.js_urls)

        except Exception as e:
            print(f"[!] 페이지 크롤링 실패: {e}")
            return []

    def download_js_files(self, output_dir: str) -> List[str]:
        """
        수집된 JavaScript 파일을 다운로드합니다.

        Args:
            output_dir: 다운로드할 디렉토리 경로

        Returns:
            다운로드된 파일 경로 리스트
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        downloaded_files = []

        for i, js_url in enumerate(self.js_urls, 1):
            try:
                print(f"[{i}/{len(self.js_urls)}] 다운로드 중: {js_url}")

                response = self.session.get(js_url, timeout=self.timeout)
                response.raise_for_status()

                # 파일명 생성 (URL 경로 기반)
                parsed = urlparse(js_url)
                filename = parsed.path.replace('/', '_').strip('_')
                if not filename or filename == '':
                    filename = f"script_{i}.js"
                if not filename.endswith('.js'):
                    filename += '.js'

                file_path = output_path / filename

                # 파일 저장
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)

                downloaded_files.append(str(file_path))
                self.js_contents[js_url] = response.text

                # 요청 간격 (서버 부하 방지)
                time.sleep(0.5)

            except Exception as e:
                print(f"[!] 다운로드 실패 ({js_url}): {e}")
                continue

        print(f"[+] 다운로드 완료: {len(downloaded_files)}개 파일")
        return downloaded_files

    def _is_same_domain(self, url: str) -> bool:
        """
        URL이 base_url과 같은 도메인인지 확인합니다.

        Args:
            url: 확인할 URL

        Returns:
            같은 도메인이면 True
        """
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc

        # 도메인이 비어있으면 (상대 경로) 같은 도메인으로 간주
        if not url_domain:
            return True

        return base_domain == url_domain

    def get_statistics(self) -> dict:
        """
        수집 통계를 반환합니다.

        Returns:
            통계 딕셔너리
        """
        return {
            'total_js_files': len(self.js_urls),
            'downloaded_files': len(self.js_contents),
            'js_urls': list(self.js_urls)
        }
