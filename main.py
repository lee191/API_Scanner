"""Shadow API Scanner - Main entry point."""

import click
import sys
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style
from tqdm import tqdm

from src.proxy.capture import ProxyRunner
from src.analyzer.js_analyzer import JSAnalyzer
from src.analyzer.endpoint_collector import EndpointCollector
from src.scanner.vulnerability_scanner import VulnerabilityScanner
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
        scan_start=datetime.now(),
        endpoints=all_endpoints
    )
    scan_result.finalize()

    reporter = ReportGenerator()
    reporter.generate_all(scan_result, prefix="js_analysis")


@cli.command()
@click.argument('url')
@click.option('--timeout', default=10, help='요청 타임아웃 (초)')
@click.option('--skip-scan', is_flag=True, help='취약점 스캔 건너뛰기')
def scan(url, timeout, skip_scan):
    """URL의 API 엔드포인트를 스캔하고 보안 취약점 검사"""
    print(f"{Fore.GREEN}[*] 대상 스캔: {url}{Style.RESET_ALL}\n")

    # Create scan result
    scan_result = ScanResult(
        target=url,
        scan_start=datetime.now()
    )

    # TODO: Implement URL crawling and endpoint discovery
    print(f"{Fore.YELLOW}[!] URL 크롤링 기능은 향후 추가 예정{Style.RESET_ALL}")

    if not skip_scan:
        print(f"\n{Fore.GREEN}[*] 보안 취약점 스캔 시작...{Style.RESET_ALL}")
        scanner = VulnerabilityScanner(timeout=timeout)

        # For now, just show scanner is ready
        print(f"{Fore.CYAN}[+] 스캐너 준비 완료{Style.RESET_ALL}")

    scan_result.finalize()


@cli.command()
@click.argument('proxy_capture', type=click.Path(exists=True))
@click.argument('js_analysis', type=click.Path(exists=True))
@click.option('--scan-vulns', is_flag=True, help='취약점 스캔 수행')
def combine(proxy_capture, js_analysis, scan_vulns):
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
@click.option('--scan-vulns/--no-scan-vulns', default=True, help='취약점 스캔 수행 여부')
@click.option('--output', default='output', help='출력 디렉토리')
def full_scan(target, js_path, scan_vulns, output):
    """전체 스캔 수행 (JS 분석 + 취약점 스캔 + 리포트)"""
    print(f"{Fore.GREEN}[*] 전체 스캔 시작: {target}{Style.RESET_ALL}\n")

    scan_result = ScanResult(
        target=target,
        scan_start=datetime.now()
    )

    collector = EndpointCollector()

    # JavaScript 수집 및 분석
    print(f"{Fore.CYAN}[1/4] JavaScript 파일 수집 중...{Style.RESET_ALL}")

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
        js_collector = JSCollector(target)
        js_collector.collect_from_page()
        downloaded_files = js_collector.download_js_files(str(temp_js_dir))
        files = [Path(f) for f in downloaded_files]

    if files:
        print(f"{Fore.GREEN}  [OK] 수집된 JS 파일: {len(files)}개{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}[2/4] JavaScript 분석 중...{Style.RESET_ALL}")
        analyzer = JSAnalyzer()

        for file in tqdm(files, desc="파일 분석"):
            endpoints = analyzer.analyze_file(str(file), target)
            collector.add_endpoints(endpoints)

        print(f"{Fore.GREEN}  [OK] 발견된 엔드포인트: {len(collector.get_endpoints())}개{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.YELLOW}  [!] JavaScript 파일을 찾을 수 없습니다{Style.RESET_ALL}\n")

    # Vulnerability scanning
    if scan_vulns and collector.get_endpoints():
        print(f"{Fore.CYAN}[3/4] 보안 취약점 스캔 중...{Style.RESET_ALL}")
        scanner = VulnerabilityScanner()

        endpoints = collector.get_endpoints()
        for endpoint in tqdm(endpoints, desc="엔드포인트 스캔"):
            try:
                vulns = scanner.scan_endpoint(endpoint)
                scan_result.vulnerabilities.extend(vulns)
            except Exception as e:
                continue

        vuln_stats = scanner.get_statistics()
        print(f"{Fore.GREEN}  [OK] 발견된 취약점: {vuln_stats['total']}개{Style.RESET_ALL}")
        if vuln_stats['critical'] > 0:
            print(f"{Fore.RED}    - Critical: {vuln_stats['critical']}개{Style.RESET_ALL}")
        if vuln_stats['high'] > 0:
            print(f"{Fore.YELLOW}    - High: {vuln_stats['high']}개{Style.RESET_ALL}")
        print()

    # Add endpoints to result
    scan_result.endpoints = collector.get_endpoints()
    scan_result.finalize()

    # Generate reports
    print(f"{Fore.CYAN}[4/4] 리포트 생성 중...{Style.RESET_ALL}")
    reporter = ReportGenerator(output_dir=output)
    reports = reporter.generate_all(scan_result, prefix="full_scan")

    print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[OK] 스캔 완료!{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}[*] 결과 요약:{Style.RESET_ALL}")
    print(f"  - 엔드포인트: {scan_result.statistics['total_endpoints']}개")
    print(f"  - 취약점: {scan_result.statistics['total_vulnerabilities']}개")
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
