"""Shadow API Scanner - Main entry point."""

import click
import sys
import io
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """Get current time in KST."""
    return datetime.now(KST)
from colorama import init, Fore, Style
from tqdm import tqdm

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.proxy.capture import ProxyRunner
from src.analyzer.js_analyzer import JSAnalyzer
from src.analyzer.endpoint_collector import EndpointCollector
from src.reporter.report_generator import ReportGenerator
from src.crawler.js_collector import JSCollector
from src.utils.models import ScanResult
from src.utils.config import get_config

# Initialize colorama
init(autoreset=True)


def print_banner():
    """Print tool banner."""
    banner = f"""
{Fore.CYAN}==============================================================

              Shadow API Scanner v1.0
         Penetration Testing Tool for API Discovery

=============================================================={Style.RESET_ALL}
"""
    print(banner)


@click.group()
def cli():
    """Shadow API Scanner - 웹 애플리케이션의 숨겨진 API 탐색 및 보안 취약점 분석 도구"""
    print_banner()


@cli.command()
@click.option('--host', default='127.0.0.1', help='프록시 호스트')
@click.option('--port', default=8080, help='프록시 포트')
def proxy(host, port):
    """프록시 서버를 시작하여 네트워크 트래픽 캡처"""
    print(f"{Fore.GREEN}[*] 프록시 서버 시작...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] 브라우저 프록시 설정: {host}:{port}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Ctrl+C로 중지{Style.RESET_ALL}\n")

    runner = ProxyRunner(host=host, port=port)
    try:
        runner.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}[*] 프록시 서버 중지됨{Style.RESET_ALL}")
        endpoints = runner.get_endpoints()
        print(f"{Fore.CYAN}[+] 수집된 엔드포인트: {len(endpoints)}개{Style.RESET_ALL}")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--base-url', default='', help='기본 URL')
@click.option('--recursive', is_flag=True, help='하위 디렉토리 포함')
def analyze(path, base_url, recursive):
    """JavaScript 파일 정적 분석으로 API 엔드포인트 추출"""
    print(f"{Fore.GREEN}[*] JavaScript 분석 시작: {path}{Style.RESET_ALL}\n")

    analyzer = JSAnalyzer()
    collector = EndpointCollector()

    path_obj = Path(path)
    files = []

    if path_obj.is_file():
        files = [path_obj]
    elif path_obj.is_dir():
        pattern = '**/*.js' if recursive else '*.js'
        files = list(path_obj.glob(pattern))

    print(f"{Fore.CYAN}[*] 분석할 파일: {len(files)}개{Style.RESET_ALL}\n")

    for file in tqdm(files, desc="분석 중"):
        endpoints = analyzer.analyze_file(str(file), base_url)
        collector.add_endpoints(endpoints)

    all_endpoints = collector.get_endpoints()
    stats = collector.get_statistics()

    print(f"\n{Fore.GREEN}[+] 분석 완료!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[+] 발견된 엔드포인트: {stats['total']}개{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[+] 메서드별:{Style.RESET_ALL}")
    for method, count in stats['by_method'].items():
        print(f"  - {method}: {count}개")

    # Save results
    scan_result = ScanResult(
        target=str(path),
        scan_start=get_kst_now(),
        endpoints=all_endpoints
    )
    scan_result.finalize()

    reporter = ReportGenerator()
    reporter.generate_all(scan_result, prefix="js_analysis")


@cli.command()
@click.argument('url')
@click.option('--timeout', default=10, help='요청 타임아웃 (초)')
def scan(url, timeout):
    """URL의 API 엔드포인트를 스캔"""
    print(f"{Fore.GREEN}[*] 대상 스캔: {url}{Style.RESET_ALL}\n")

    # Create scan result
    scan_result = ScanResult(
        target=url,
        scan_start=get_kst_now()
    )

    # TODO: Implement URL crawling and endpoint discovery
    print(f"{Fore.YELLOW}[!] URL 크롤링 기능은 향후 추가 예정{Style.RESET_ALL}")

    scan_result.finalize()


@cli.command()
@click.argument('proxy_capture', type=click.Path(exists=True))
@click.argument('js_analysis', type=click.Path(exists=True))
def combine(proxy_capture, js_analysis):
    """프록시 캡처와 JS 분석 결과 결합"""
    print(f"{Fore.GREEN}[*] 결과 결합 중...{Style.RESET_ALL}\n")

    collector = EndpointCollector()

    # Load proxy capture results
    # TODO: Implement loading from saved proxy data

    # Load JS analysis results
    # TODO: Implement loading from saved JS analysis data

    print(f"{Fore.YELLOW}[!] 결과 결합 기능은 향후 추가 예정{Style.RESET_ALL}")


@cli.command()
@click.argument('target')
@click.option('--js-path', type=click.Path(exists=True), help='JavaScript 파일/디렉토리')
@click.option('--bruteforce/--no-bruteforce', default=False, help='디렉토리 브루트포싱 활성화')
@click.option('--wordlist', type=click.Path(exists=True), help='브루트포싱 wordlist 경로')
@click.option('--validate/--no-validate', default=True, help='엔드포인트 HTTP 검증 활성화')
@click.option('--ai/--no-ai', default=False, help='AI 기반 분석 및 검증 활성화 (정적 + AI)')
@click.option('--static-only', is_flag=True, help='정적 분석만 수행 (AI 비활성화)')
@click.option('--ai-only', is_flag=True, help='AI 분석만 수행 (정적 분석 비활성화)')
@click.option('--crawl-depth', default=1, type=int, help='크롤링 깊이 (1=현재 페이지만, 2+=재귀 크롤링)')
@click.option('--max-pages', default=50, type=int, help='최대 크롤링 페이지 수')
@click.option('--output', default='output', help='출력 디렉토리')
def full_scan(target, js_path, bruteforce, wordlist, validate, ai, static_only, ai_only, crawl_depth, max_pages, output):
    """전체 스캔 수행 (JS 분석 + 리포트)"""
    print(f"{Fore.GREEN}[*] 전체 스캔 시작: {target}{Style.RESET_ALL}\n")

    scan_result = ScanResult(
        target=target,
        scan_start=get_kst_now()
    )

    collector = EndpointCollector()

    # JavaScript 수집 및 분석
    print(f"{Fore.CYAN}[1/3] JavaScript 파일 수집 중...{Style.RESET_ALL}")

    # 임시 디렉토리 생성
    temp_js_dir = Path(output) / 'temp_js'
    temp_js_dir.mkdir(parents=True, exist_ok=True)

    files = []

    # js_path가 지정되면 해당 경로 사용, 아니면 자동 수집
    if js_path:
        print(f"[*] 지정된 경로 사용: {js_path}")
        path_obj = Path(js_path)

        if path_obj.is_file():
            files = [path_obj]
        elif path_obj.is_dir():
            files = list(path_obj.glob('**/*.js'))
    else:
        print(f"[*] 웹사이트에서 자동 수집: {target}")
        if bruteforce:
            print(f"{Fore.YELLOW}[*] 디렉토리 브루트포싱 활성화됨{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] 크롤링 깊이: {crawl_depth}, 최대 페이지: {max_pages}{Style.RESET_ALL}")
        
        js_collector = JSCollector(
            target, 
            enable_bruteforce=bruteforce, 
            wordlist_path=wordlist,
            crawl_depth=crawl_depth,
            max_pages=max_pages
        )

        # 브루트포싱이 활성화되면 collect_with_bruteforce 사용
        if bruteforce:
            js_collector.collect_with_bruteforce()
        else:
            js_collector.collect_from_page()

        downloaded_files = js_collector.download_js_files(str(temp_js_dir))
        files = [Path(f) for f in downloaded_files]

        # 통계 출력
        stats = js_collector.get_statistics()
        print(f"{Fore.GREEN}  [OK] 크롤링한 페이지: {stats['crawled_pages']}개{Style.RESET_ALL}")
        
        # 브루트포싱 통계 출력 및 발견된 경로 저장
        if bruteforce:
            scan_result.discovered_paths = js_collector.discovered_paths
            print(f"{Fore.GREEN}  [OK] 발견된 경로: {stats['discovered_paths']}개{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}  [OK] 수집된 JS 파일: {stats['total_js_files']}개{Style.RESET_ALL}\n")

    if files:
        print(f"{Fore.GREEN}  [OK] 수집된 JS 파일: {len(files)}개{Style.RESET_ALL}\n")

        # 정적 분석 (ai_only가 아닌 경우에만)
        if not ai_only:
            print(f"{Fore.CYAN}[2/3] JavaScript 정적 분석 중...{Style.RESET_ALL}")
            analyzer = JSAnalyzer()

            for file in tqdm(files, desc="파일 분석"):
                endpoints = analyzer.analyze_file(str(file), target)
                # Mark as static analysis
                for ep in endpoints:
                    if not ep.source.startswith('AI'):
                        ep.source = f"Static:{ep.source}"
                collector.add_endpoints(endpoints)

            print(f"{Fore.GREEN}  [OK] 발견된 엔드포인트: {len(collector.get_endpoints())}개{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.YELLOW}  [!] JavaScript 파일을 찾을 수 없습니다{Style.RESET_ALL}\n")

    # Validate endpoints
    all_endpoints = collector.get_endpoints()

    if validate and all_endpoints:
        validation_step = "[2.5/4]" if ai else "[2.5/3]"
        print(f"{Fore.CYAN}{validation_step} 엔드포인트 검증 중...{Style.RESET_ALL}")
        from src.utils.endpoint_validator import EndpointValidator

        validator = EndpointValidator(timeout=5)

        valid_count = 0
        invalid_count = 0

        # Validate each endpoint with progress bar
        for endpoint in tqdm(all_endpoints, desc="검증 중"):
            is_valid, status_code, response = validator.validate_endpoint(endpoint)

            # Update endpoint with validation result
            endpoint.status_code = status_code
            endpoint.response_example = response

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        validator.close()

        # Print validation summary
        print(f"{Fore.GREEN}  [OK] 검증 완료{Style.RESET_ALL}")
        print(f"{Fore.GREEN}    - 유효한 엔드포인트: {valid_count}개 ({valid_count*100//(valid_count+invalid_count) if (valid_count+invalid_count) > 0 else 0}%){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}    - 무효한 엔드포인트 (False Positive): {invalid_count}개 ({invalid_count*100//(valid_count+invalid_count) if (valid_count+invalid_count) > 0 else 0}%){Style.RESET_ALL}\n")

    # AI Analysis (if enabled or ai_only)
    if (ai or ai_only) and files and not static_only:
        print(f"{Fore.CYAN}[3/4] AI 기반 엔드포인트 추론 중...{Style.RESET_ALL}")
        ai_model = os.getenv('AI_MODEL', 'gpt-4o')
        print(f"{Fore.YELLOW}  [AI] {ai_model}를 사용하여 숨겨진 엔드포인트 추론{Style.RESET_ALL}")

        try:
            from src.analyzer.ai_analyzer import analyze_js_with_ai

            # Convert Path objects to strings
            js_file_paths = [str(f) for f in files]

            # AI analyzes JS files and infers hidden endpoints
            ai_endpoints = analyze_js_with_ai(js_file_paths, target)

            if ai_endpoints:
                print(f"{Fore.GREEN}  [OK] AI 추론 완료{Style.RESET_ALL}")
                print(f"{Fore.CYAN}    - AI가 추론하고 검증한 엔드포인트: {len(ai_endpoints)}개{Style.RESET_ALL}")

                # Get existing static endpoints for comparison
                existing_endpoints = collector.get_endpoints()
                existing_urls = {ep.url for ep in existing_endpoints}

                # Mark AI endpoints with AI prefix only if not found in static analysis
                ai_only_count = 0
                both_found_count = 0
                for ep in ai_endpoints:
                    if ep.url in existing_urls:
                        # Found in both static and AI - keep as Static only (no AI badge)
                        both_found_count += 1
                        # Don't add AI prefix
                    else:
                        # AI only - mark with AI prefix
                        ai_only_count += 1
                        if not ep.source.startswith('AI'):
                            ep.source = f"AI:{ep.source}"

                # Add AI-inferred endpoints to collector
                collector.add_endpoints(ai_endpoints)
                
                if both_found_count > 0:
                    print(f"{Fore.GREEN}    - 정적 분석과 일치: {both_found_count}개 (AI 배지 제외){Style.RESET_ALL}")
                if ai_only_count > 0:
                    print(f"{Fore.MAGENTA}    - AI만 발견: {ai_only_count}개 (AI 배지 표시){Style.RESET_ALL}")

                # Update all_endpoints to include AI-inferred ones
                all_endpoints = collector.get_endpoints()

                if ai_only:
                    print(f"{Fore.CYAN}    - AI 분석 엔드포인트: {len(all_endpoints)}개{Style.RESET_ALL}\n")
                else:
                    print(f"{Fore.CYAN}    - 총 엔드포인트 (정적 분석 + AI 추론): {len(all_endpoints)}개{Style.RESET_ALL}\n")
            else:
                print(f"{Fore.YELLOW}  [!] AI가 추가 엔드포인트를 발견하지 못했습니다{Style.RESET_ALL}\n")

        except Exception as e:
            print(f"{Fore.YELLOW}  [!] AI 분석 실패: {e}{Style.RESET_ALL}\n")

    # Add endpoints to result
    scan_result.endpoints = all_endpoints
    scan_result.finalize()

    # Save to database
    try:
        from src.database.connection import get_db, init_db
        from src.database.repository import ScanRepository
        from uuid import uuid4
        
        # Initialize database
        init_db()
        
        # Save scan result to database
        with get_db() as db:
            scan_id = str(uuid4())
            scan = ScanRepository.create_scan(
                db=db,
                scan_id=scan_id,
                target_url=target,
                js_path=js_path,
                scan_vulns=ai,
                ai_enabled=ai,
                bruteforce_enabled=bruteforce,
                analysis_type='full_scan'
            )
            
            # Save scan result
            ScanRepository.save_scan_result(
                db=db,
                scan_id=scan_id,
                scan_result=scan_result
            )
            
            print(f"{Fore.GREEN}  [OK] 데이터베이스 저장 완료 (scan_id: {scan_id}){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}  [!] 데이터베이스 저장 실패: {e}{Style.RESET_ALL}")

    # Generate reports
    report_step = "[4/4]" if ai else "[3/3]"
    print(f"{Fore.CYAN}{report_step} 리포트 생성 중...{Style.RESET_ALL}")
    reporter = ReportGenerator(output_dir=output)
    reports = reporter.generate_all(scan_result, prefix="full_scan")

    print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[OK] 스캔 완료!{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}[*] 결과 요약:{Style.RESET_ALL}")
    print(f"  - 엔드포인트: {scan_result.statistics['total_endpoints']}개")
    print(f"\n{Fore.CYAN}[*] 생성된 리포트:{Style.RESET_ALL}")
    for format_type, path in reports.items():
        print(f"  - {format_type.upper()}: {path}")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] 사용자에 의해 중단됨{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[!] 오류 발생: {e}{Style.RESET_ALL}")
        sys.exit(1)
