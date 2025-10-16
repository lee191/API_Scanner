"""Extract all endpoints from JavaScript files and save to txt file."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analyzer.js_analyzer import JSAnalyzer
import glob

def extract_endpoints_to_txt(js_path: str, output_file: str = "endpoints.txt"):
    """Extract all endpoints from JS files and save to txt file."""

    print(f"[*] JavaScript 파일 경로: {js_path}")

    # Initialize analyzer
    analyzer = JSAnalyzer()

    # Collect JS files
    js_files = list(glob.glob(f"{js_path}/**/*.js", recursive=True))
    print(f"[+] 발견된 JS 파일: {len(js_files)}개")

    # Analyze files
    all_endpoints = []
    for js_file in js_files:
        endpoints = analyzer.analyze_file(js_file)
        all_endpoints.extend(endpoints)

    print(f"[+] 발견된 엔드포인트: {len(all_endpoints)}개")
    endpoints = all_endpoints

    # Prepare output
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("JavaScript 파일에서 추출된 모든 API 엔드포인트")
    output_lines.append("=" * 80)
    output_lines.append(f"분석 경로: {js_path}")
    output_lines.append(f"총 JS 파일: {len(js_files)}개")
    output_lines.append(f"총 엔드포인트: {len(endpoints)}개")
    output_lines.append("=" * 80)
    output_lines.append("")

    # Group endpoints by method
    endpoints_by_method = {}
    for ep in endpoints:
        method = ep.method.value if hasattr(ep.method, 'value') else str(ep.method)
        if method not in endpoints_by_method:
            endpoints_by_method[method] = []
        endpoints_by_method[method].append(ep)

    # Write endpoints by method
    for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        if method in endpoints_by_method:
            eps = endpoints_by_method[method]
            output_lines.append(f"[{method}] ({len(eps)}개)")
            output_lines.append("-" * 80)
            for ep in sorted(eps, key=lambda x: x.url):
                output_lines.append(f"  {ep.url}")
                if ep.parameters:
                    output_lines.append(f"    Parameters: {', '.join(ep.parameters.keys())}")
                output_lines.append(f"    Source: {ep.source}")
                output_lines.append("")

    # Write all endpoints as simple list
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("전체 엔드포인트 목록 (URL만)")
    output_lines.append("=" * 80)
    for ep in sorted(endpoints, key=lambda x: (x.method.value if hasattr(x.method, 'value') else str(x.method), x.url)):
        method = ep.method.value if hasattr(ep.method, 'value') else str(ep.method)
        output_lines.append(f"{method:8s} {ep.url}")

    # Save to file
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n[+] 엔드포인트 목록 저장: {output_path}")
    print(f"    - 총 {len(endpoints)}개 엔드포인트")
    print(f"    - GET: {len(endpoints_by_method.get('GET', []))}개")
    print(f"    - POST: {len(endpoints_by_method.get('POST', []))}개")
    print(f"    - PUT: {len(endpoints_by_method.get('PUT', []))}개")
    print(f"    - PATCH: {len(endpoints_by_method.get('PATCH', []))}개")
    print(f"    - DELETE: {len(endpoints_by_method.get('DELETE', []))}개")

    return str(output_path)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_endpoints.py <js_path> [output_file]")
        print("Example: python extract_endpoints.py test-app/static endpoints.txt")
        sys.exit(1)

    js_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "endpoints.txt"

    extract_endpoints_to_txt(js_path, output_file)
