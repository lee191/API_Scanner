"""JavaScript 파일 자동 수집 모듈."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
import re
import time

from src.crawler.directory_bruteforcer import DirectoryBruteForcer


class JSCollector:
    """웹사이트에서 JavaScript 파일을 자동으로 수집하는 클래스."""

    def __init__(self, base_url: str, timeout: int = 10, enable_bruteforce: bool = False,
                 wordlist_path: Optional[str] = None, include_subdomains: bool = True,
                 include_external_js: bool = False, crawl_depth: int = 1, max_pages: int = 50):
        """
        Args:
            base_url: 대상 웹사이트 URL
            timeout: 요청 타임아웃 (초)
            enable_bruteforce: 디렉토리 브루트포싱 활성화 여부
            wordlist_path: 브루트포싱에 사용할 wordlist 경로 (기본값: 내장 wordlist)
            include_subdomains: 서브도메인 포함 여부 (cdn.example.com 등)
            include_external_js: 외부 JS 파일 포함 여부 (CDN, 3rd party 등)
            crawl_depth: 크롤링 깊이 (1=현재 페이지만, 2=링크된 페이지 포함, 3+=재귀 크롤링)
            max_pages: 최대 크롤링 페이지 수 (무한 크롤링 방지)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.enable_bruteforce = enable_bruteforce
        self.include_subdomains = include_subdomains
        self.include_external_js = include_external_js
        self.crawl_depth = crawl_depth
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.js_urls: Set[str] = set()
        self.js_contents: dict = {}
        self.discovered_paths: List[Dict[str, Any]] = []
        self.visited_urls: Set[str] = set()  # 크롤링한 URL 추적
        self.crawled_pages: int = 0  # 크롤링한 페이지 수

        # 디렉토리 브루트포서 초기화
        if enable_bruteforce:
            self.bruteforcer = DirectoryBruteForcer(base_url, wordlist_path, timeout)
        else:
            self.bruteforcer = None

    def collect_from_page(self, url: str = None, current_depth: int = 0) -> List[str]:
        """
        페이지에서 JavaScript 파일 URL을 수집합니다. (재귀 크롤링 지원)

        Args:
            url: 수집할 페이지 URL (기본값: base_url)
            current_depth: 현재 크롤링 깊이

        Returns:
            수집된 JavaScript 파일 URL 리스트
        """
        if url is None:
            url = self.base_url

        # 크롤링 제한 체크
        if current_depth >= self.crawl_depth:
            return list(self.js_urls)
        
        if self.crawled_pages >= self.max_pages:
            print(f"[!] 최대 페이지 수({self.max_pages}) 도달")
            return list(self.js_urls)
        
        if url in self.visited_urls:
            return list(self.js_urls)

        try:
            print(f"[*] 페이지 크롤링 (깊이 {current_depth + 1}/{self.crawl_depth}): {url}")
            self.visited_urls.add(url)
            self.crawled_pages += 1
            
            response = self.session.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()
            print(f"[+] 페이지 로드 성공 (상태 코드: {response.status_code})")

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 다음 단계에서 크롤링할 URL 수집
            next_urls = []

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

            # <a> 태그에서 링크 수집 (재귀 크롤링용)
            if current_depth + 1 < self.crawl_depth:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    # 같은 도메인이고 아직 방문하지 않은 HTML 페이지
                    if self._is_same_domain(full_url) and full_url not in self.visited_urls:
                        # 파일 확장자 체크 (HTML 페이지만)
                        parsed = urlparse(full_url)
                        path = parsed.path.lower()
                        
                        # JS, CSS, 이미지 등 제외
                        if not any(path.endswith(ext) for ext in ['.js', '.css', '.jpg', '.png', '.gif', '.svg', '.ico', '.pdf', '.zip']):
                            # 서버 사이드 스크립트 포함
                            if path.endswith('.jsp') or path.endswith('.asp') or path.endswith('.aspx') or path.endswith('.php'):
                                self.js_urls.add(full_url)
                                print(f"[+] 서버 스크립트 발견: {full_url}")
                            else:
                                next_urls.append(full_url)

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

            print(f"[+] 현재까지 발견된 JS 파일: {len(self.js_urls)}개")
            
            # 재귀 크롤링
            if next_urls and current_depth + 1 < self.crawl_depth:
                print(f"[*] 다음 깊이 크롤링: {len(next_urls)}개 링크")
                for next_url in next_urls[:10]:  # 페이지당 최대 10개 링크만
                    if self.crawled_pages >= self.max_pages:
                        break
                    self.collect_from_page(next_url, current_depth + 1)
            
            return list(self.js_urls)

        except Exception as e:
            print(f"[!] 페이지 크롤링 실패: {e}")
            return list(self.js_urls)

    def collect_with_bruteforce(self) -> List[str]:
        """
        디렉토리 브루트포싱을 통해 숨겨진 경로를 발견하고,
        각 경로에서 JavaScript 파일을 수집합니다.

        Returns:
            수집된 JavaScript 파일 URL 리스트
        """
        if not self.enable_bruteforce or not self.bruteforcer:
            print("[!] 브루트포싱이 비활성화되어 있습니다.")
            return self.collect_from_page()

        # 1. 기본 페이지에서 JS 수집
        print("\n[*] 기본 페이지에서 JavaScript 파일 수집 중...")
        self.collect_from_page()

        # 2. 디렉토리 브루트포싱 수행
        print("\n[*] 디렉토리 브루트포싱 시작...")
        self.discovered_paths = self.bruteforcer.brute_force()

        # 3. 발견된 경로에서 JS 파일 자동 크롤링 (브루트포서 기능 사용)
        if self.discovered_paths:
            print(f"\n[*] 발견된 {len(self.discovered_paths)}개 경로에서 JS 파일 크롤링 중...")

            # 브루트포서의 자동 크롤링 기능 사용
            newly_discovered_js = self.bruteforcer.crawl_discovered_paths()

            # 발견된 JS 파일을 js_urls에 추가 (중복 제거)
            for js_url in newly_discovered_js:
                if self._is_same_domain(js_url):
                    self.js_urls.add(js_url)

            # 브루트포서에서 발견한 모든 JS 파일도 추가
            all_bruteforce_js = self.bruteforcer.get_discovered_js_files()
            for js_url in all_bruteforce_js:
                if self._is_same_domain(js_url):
                    self.js_urls.add(js_url)

            print(f"[+] 브루트포싱으로 추가 발견된 JS: {len(newly_discovered_js)}개")

        print(f"\n[+] 브루트포싱 수집 완료: 총 {len(self.js_urls)}개 JS 파일 발견")
        return list(self.js_urls)

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
        # 외부 JS 포함 옵션이 활성화되면 모든 JS 수집
        if self.include_external_js:
            return True

        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc

        # 도메인이 비어있으면 (상대 경로) 같은 도메인으로 간주
        if not url_domain:
            return True

        # 완전히 같은 도메인
        if base_domain == url_domain:
            return True

        # 서브도메인 포함 옵션이 활성화된 경우
        if self.include_subdomains:
            # 루트 도메인 추출 (예: www.naver.com → naver.com)
            base_root = self._get_root_domain(base_domain)
            url_root = self._get_root_domain(url_domain)

            if base_root and url_root and base_root == url_root:
                return True

        return False

    def _get_root_domain(self, domain: str) -> Optional[str]:
        """
        루트 도메인을 추출합니다.

        예:
        - www.naver.com → naver.com
        - cdn.naver.com → naver.com
        - api.example.co.kr → example.co.kr
        - localhost:5000 → localhost

        Args:
            domain: 도메인 문자열

        Returns:
            루트 도메인 또는 None
        """
        if not domain:
            return None

        # 포트 제거
        if ':' in domain:
            domain = domain.split(':')[0]

        # localhost 처리
        if domain == 'localhost' or domain.startswith('127.') or domain.startswith('192.168.'):
            return domain

        # IP 주소 처리
        if all(part.isdigit() for part in domain.split('.')):
            return domain

        # 도메인 파트 분리
        parts = domain.split('.')

        # .co.kr, .ac.kr 등 2단계 TLD 처리
        if len(parts) >= 3 and parts[-2] in ['co', 'ac', 'go', 'or', 'ne']:
            return '.'.join(parts[-3:])

        # 일반적인 경우 (최상위 2단계만)
        if len(parts) >= 2:
            return '.'.join(parts[-2:])

        return domain

    def get_statistics(self) -> dict:
        """
        수집 통계를 반환합니다.

        Returns:
            통계 딕셔너리
        """
        return {
            'total_js_files': len(self.js_urls),
            'downloaded_files': len(self.js_contents),
            'js_urls': list(self.js_urls),
            'bruteforce_enabled': self.enable_bruteforce,
            'discovered_paths': len(self.discovered_paths),
            'discovered_path_urls': self.discovered_paths,
            'crawl_depth': self.crawl_depth,
            'crawled_pages': self.crawled_pages,
            'max_pages': self.max_pages
        }
