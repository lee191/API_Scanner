"""Extract endpoints from specific JavaScript files."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analyzer.js_analyzer import JSAnalyzer

def extract_endpoints_from_files(file_paths: list, output_file: str = "endpoints_specific.txt"):
    """Extract all endpoints from specific JS files and save to txt file."""

    print(f"[*] 분석할 파일: {len(file_paths)}개")
    for fp in file_paths:
        print(f"    - {fp}")

    # Initialize analyzer
    analyzer = JSAnalyzer()

    # Analyze files
    all_endpoints = []
    file_endpoint_counts = {}

    for js_file in file_paths:
        if not Path(js_file).exists():
            print(f"[!] 파일을 찾을 수 없습니다: {js_file}")
            continue

        endpoints = analyzer.analyze_file(js_file)
        all_endpoints.extend(endpoints)
        file_endpoint_counts[js_file] = len(endpoints)
        print(f"    [+] {Path(js_file).name}: {len(endpoints)}개 엔드포인트")

    print(f"\n[+] 총 발견된 엔드포인트: {len(all_endpoints)}개")

    # Prepare output
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("특정 JavaScript 파일에서 추출된 API 엔드포인트")
    output_lines.append("=" * 80)
    output_lines.append(f"분석 파일 개수: {len(file_paths)}개")
    output_lines.append("")
    for fp in file_paths:
        count = file_endpoint_counts.get(fp, 0)
        output_lines.append(f"  - {Path(fp).name}: {count}개")
    output_lines.append("")
    output_lines.append(f"총 엔드포인트: {len(all_endpoints)}개")
    output_lines.append("=" * 80)
    output_lines.append("")

    # Group endpoints by file
    endpoints_by_file = {}
    for ep in all_endpoints:
        source = ep.source
        if source not in endpoints_by_file:
            endpoints_by_file[source] = []
        endpoints_by_file[source].append(ep)

    # Write endpoints by file
    for file_path in file_paths:
        if file_path not in endpoints_by_file:
            continue

        eps = endpoints_by_file[file_path]
        output_lines.append("")
        output_lines.append("=" * 80)
        output_lines.append(f"파일: {Path(file_path).name}")
        output_lines.append(f"경로: {file_path}")
        output_lines.append(f"엔드포인트 개수: {len(eps)}개")
        output_lines.append("=" * 80)
        output_lines.append("")

        # Group by method
        endpoints_by_method = {}
        for ep in eps:
            method = ep.method.value if hasattr(ep.method, 'value') else str(ep.method)
            if method not in endpoints_by_method:
                endpoints_by_method[method] = []
            endpoints_by_method[method].append(ep)

        # Write by method
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            if method in endpoints_by_method:
                method_eps = endpoints_by_method[method]
                output_lines.append(f"[{method}] ({len(method_eps)}개)")
                output_lines.append("-" * 80)
                for ep in sorted(method_eps, key=lambda x: x.url):
                    output_lines.append(f"  {ep.url}")
                    if ep.parameters:
                        output_lines.append(f"    Parameters: {', '.join(ep.parameters.keys())}")
                output_lines.append("")

    # Write all endpoints as simple list
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("전체 엔드포인트 목록 (간단)")
    output_lines.append("=" * 80)

    # Group by method for summary
    endpoints_by_method = {}
    for ep in all_endpoints:
        method = ep.method.value if hasattr(ep.method, 'value') else str(ep.method)
        if method not in endpoints_by_method:
            endpoints_by_method[method] = []
        endpoints_by_method[method].append(ep)

    for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        if method in endpoints_by_method:
            output_lines.append(f"\n[{method}] ({len(endpoints_by_method[method])}개)")
            output_lines.append("-" * 80)
            for ep in sorted(endpoints_by_method[method], key=lambda x: x.url):
                output_lines.append(f"{method:8s} {ep.url}")

    # Save to file
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n[+] 엔드포인트 목록 저장: {output_path}")
    print(f"    - 총 {len(all_endpoints)}개 엔드포인트")
    for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        count = len(endpoints_by_method.get(method, []))
        if count > 0:
            print(f"    - {method}: {count}개")

    return str(output_path)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_specific_files.py <file1> <file2> ... [output_file]")
        print("Example: python extract_specific_files.py auth.js main.js shop.js endpoints.txt")
        sys.exit(1)

    # Check if last argument is output file (ends with .txt)
    if sys.argv[-1].endswith('.txt'):
        file_paths = sys.argv[1:-1]
        output_file = sys.argv[-1]
    else:
        file_paths = sys.argv[1:]
        output_file = "endpoints_specific.txt"

    extract_endpoints_from_files(file_paths, output_file)
