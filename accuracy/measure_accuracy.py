"""Measure endpoint detection accuracy by comparing scan results with ground truth."""

import re
from pathlib import Path
from typing import Set, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs, urlencode

def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison.

    - Remove protocol and domain (http://localhost:5000)
    - Convert to lowercase
    - Sort query parameters
    - Normalize path parameters
    """
    # Remove whitespace
    url = url.strip()

    # Remove protocol and domain
    if url.startswith('http://') or url.startswith('https://'):
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query

        # Reconstruct without domain
        if query:
            url = f"{path}?{query}"
        else:
            url = path

    # Convert to lowercase
    url = url.lower()

    # Normalize query parameters (sort them)
    if '?' in url:
        path, query_string = url.split('?', 1)

        # Parse query parameters
        params = []
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params.append((key, value))
            else:
                params.append((param, ''))

        # Sort and reconstruct
        params.sort()
        if params:
            query_string = '&'.join([f"{k}={v}" if v else k for k, v in params])
            url = f"{path}?{query_string}"
        else:
            url = path

    # Remove trailing slash
    url = url.rstrip('/')

    return url

def parse_endpoints_from_txt(file_path: str) -> Set[str]:
    """
    Parse endpoints from txt file.

    Handles multiple formats:
    - Plain URL list (scan_result.txt)
    - Formatted output with METHOD URL (endpoints.txt)
    """
    endpoints = set()

    if not Path(file_path).exists():
        print(f"[!] File not found: {file_path}")
        return endpoints

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and section headers
            if not line or line.startswith('=') or line.startswith('-') or line.startswith('['):
                continue

            # Skip metadata lines
            if any(x in line for x in ['분석 경로:', '총 JS 파일:', '총 엔드포인트:', 'Parameters:', 'Source:', '파일:', '경로:', '엔드포인트 개수:', '분석 파일', '파일에서 추출된', '엔드포인트 목록']):
                continue

            # Skip summary lines
            if line.startswith('- ') or line.startswith('  -'):
                continue

            # Skip lines with colons ONLY if they look like metadata (not path parameters)
            # Path parameters like /api/:id are valid, headers like "파일: xyz" are not
            if ':' in line and not line.startswith('http') and not '/api' in line and not re.search(r'[A-Z]+\s+/', line):
                continue

            # Extract URL from "METHOD URL" format
            method_pattern = r'^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(.+)$'
            match = re.match(method_pattern, line, re.IGNORECASE)

            if match:
                url = match.group(2).strip()
            else:
                # Plain URL
                url = line

            # Normalize and add
            normalized = normalize_url(url)
            if normalized:
                endpoints.add(normalized)

    return endpoints

def calculate_metrics(ground_truth: Set[str], detected: Set[str]) -> Dict[str, any]:
    """Calculate precision, recall, F1 score and related metrics."""

    # True Positives: detected AND in ground truth
    tp = ground_truth.intersection(detected)

    # False Positives: detected but NOT in ground truth
    fp = detected.difference(ground_truth)

    # False Negatives: in ground truth but NOT detected
    fn = ground_truth.difference(detected)

    # Calculate metrics
    precision = len(tp) / len(detected) if len(detected) > 0 else 0.0
    recall = len(tp) / len(ground_truth) if len(ground_truth) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'tp_count': len(tp),
        'fp_count': len(fp),
        'fn_count': len(fn),
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'ground_truth_count': len(ground_truth),
        'detected_count': len(detected)
    }

def generate_report(ground_truth_file: str, detected_file: str, output_file: str = None):
    """Generate accuracy measurement report."""

    print(f"\n{'='*80}")
    print(f"엔드포인트 탐지 정확도 측정")
    print(f"{'='*80}\n")

    # Parse files
    print(f"[*] Ground Truth 파일 로드: {ground_truth_file}")
    ground_truth = parse_endpoints_from_txt(ground_truth_file)
    print(f"    - 총 {len(ground_truth)}개 엔드포인트")

    print(f"\n[*] 탐지 결과 파일 로드: {detected_file}")
    detected = parse_endpoints_from_txt(detected_file)
    print(f"    - 총 {len(detected)}개 엔드포인트")

    # Calculate metrics
    print(f"\n[*] 정확도 계산 중...")
    metrics = calculate_metrics(ground_truth, detected)

    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("엔드포인트 탐지 정확도 측정 결과")
    report_lines.append("=" * 80)
    report_lines.append(f"Ground Truth: {Path(ground_truth_file).name}")
    report_lines.append(f"탐지 결과: {Path(detected_file).name}")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Summary metrics
    report_lines.append("## 정확도 메트릭")
    report_lines.append("")
    report_lines.append(f"Precision (정밀도):  {metrics['precision']:.2%}")
    report_lines.append(f"  - 탐지한 것 중 실제로 맞는 것의 비율")
    report_lines.append(f"  - {metrics['tp_count']} / {metrics['detected_count']}")
    report_lines.append("")
    report_lines.append(f"Recall (재현율):     {metrics['recall']:.2%}")
    report_lines.append(f"  - 실제 엔드포인트 중 탐지한 것의 비율")
    report_lines.append(f"  - {metrics['tp_count']} / {metrics['ground_truth_count']}")
    report_lines.append("")
    report_lines.append(f"F1 Score:            {metrics['f1_score']:.2%}")
    report_lines.append(f"  - Precision과 Recall의 조화평균")
    report_lines.append("")

    # Confusion matrix
    report_lines.append("## 혼동 행렬 (Confusion Matrix)")
    report_lines.append("")
    report_lines.append(f"True Positives (TP):   {metrics['tp_count']}개  - 정확히 탐지")
    report_lines.append(f"False Positives (FP):  {metrics['fp_count']}개  - 잘못 탐지")
    report_lines.append(f"False Negatives (FN):  {metrics['fn_count']}개  - 놓친 엔드포인트")
    report_lines.append("")

    # True Positives
    if metrics['true_positives']:
        report_lines.append("=" * 80)
        report_lines.append(f"## [OK] True Positives ({metrics['tp_count']}개) - 정확히 탐지한 엔드포인트")
        report_lines.append("=" * 80)
        for url in sorted(metrics['true_positives']):
            report_lines.append(f"  [+] {url}")
        report_lines.append("")

    # False Positives
    if metrics['false_positives']:
        report_lines.append("=" * 80)
        report_lines.append(f"## [X] False Positives ({metrics['fp_count']}개) - 잘못 탐지한 엔드포인트")
        report_lines.append("=" * 80)
        report_lines.append("  (실제로는 존재하지 않는데 탐지된 것)")
        report_lines.append("")
        for url in sorted(metrics['false_positives']):
            report_lines.append(f"  [-] {url}")
        report_lines.append("")

    # False Negatives
    if metrics['false_negatives']:
        report_lines.append("=" * 80)
        report_lines.append(f"## [!] False Negatives ({metrics['fn_count']}개) - 놓친 엔드포인트")
        report_lines.append("=" * 80)
        report_lines.append("  (실제로 존재하는데 탐지하지 못한 것)")
        report_lines.append("")
        for url in sorted(metrics['false_negatives']):
            report_lines.append(f"  [!] {url}")
        report_lines.append("")

    # Overall assessment
    report_lines.append("=" * 80)
    report_lines.append("## 종합 평가")
    report_lines.append("=" * 80)

    if metrics['f1_score'] >= 0.9:
        grade = "우수 (Excellent)"
    elif metrics['f1_score'] >= 0.8:
        grade = "양호 (Good)"
    elif metrics['f1_score'] >= 0.7:
        grade = "보통 (Fair)"
    else:
        grade = "개선 필요 (Needs Improvement)"

    report_lines.append(f"종합 점수: {grade}")
    report_lines.append(f"F1 Score: {metrics['f1_score']:.2%}")
    report_lines.append("")

    # Print to console
    print(f"\n{'='*80}")
    print("정확도 측정 결과")
    print(f"{'='*80}")
    print(f"Precision:  {metrics['precision']:.2%} ({metrics['tp_count']}/{metrics['detected_count']})")
    print(f"Recall:     {metrics['recall']:.2%} ({metrics['tp_count']}/{metrics['ground_truth_count']})")
    print(f"F1 Score:   {metrics['f1_score']:.2%}")
    print(f"\nTP: {metrics['tp_count']} | FP: {metrics['fp_count']} | FN: {metrics['fn_count']}")
    print(f"종합 평가: {grade}")
    print(f"{'='*80}\n")

    # Save report
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"[+] 상세 리포트 저장: {output_path}\n")

    return metrics

def compare_multiple_files(ground_truth_file: str, detected_files: List[str], output_dir: str = "accuracy"):
    """Compare multiple detection result files with ground truth."""

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    all_metrics = {}

    for detected_file in detected_files:
        file_name = Path(detected_file).stem
        output_file = output_dir / f"accuracy_{file_name}.txt"

        print(f"\n{'#'*80}")
        print(f"# 비교 대상: {Path(detected_file).name}")
        print(f"{'#'*80}")

        metrics = generate_report(ground_truth_file, detected_file, str(output_file))
        all_metrics[file_name] = metrics

    # Generate comparison summary
    if len(detected_files) > 1:
        print(f"\n{'='*80}")
        print("전체 비교 요약")
        print(f"{'='*80}\n")

        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("전체 비교 요약")
        summary_lines.append("=" * 80)
        summary_lines.append("")
        summary_lines.append(f"{'파일명':<30} {'Precision':>12} {'Recall':>12} {'F1 Score':>12}")
        summary_lines.append("-" * 80)

        for file_name, metrics in all_metrics.items():
            summary_lines.append(
                f"{file_name:<30} {metrics['precision']:>11.2%} {metrics['recall']:>11.2%} {metrics['f1_score']:>11.2%}"
            )
            print(f"{file_name:<30} P:{metrics['precision']:.2%}  R:{metrics['recall']:.2%}  F1:{metrics['f1_score']:.2%}")

        summary_lines.append("")

        # Save comparison summary
        summary_file = output_dir / "accuracy_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))

        print(f"\n[+] 비교 요약 저장: {summary_file}\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python measure_accuracy.py <ground_truth_file> <detected_file1> [detected_file2] ...")
        print("\nExample:")
        print("  python measure_accuracy.py accuracy/scan_result.txt endpoints.txt")
        print("  python measure_accuracy.py accuracy/scan_result.txt endpoints.txt endpoints_3files.txt")
        sys.exit(1)

    ground_truth_file = sys.argv[1]
    detected_files = sys.argv[2:]

    if len(detected_files) == 1:
        # Single comparison
        output_file = "accuracy_report.txt"
        generate_report(ground_truth_file, detected_files[0], output_file)
    else:
        # Multiple comparisons
        compare_multiple_files(ground_truth_file, detected_files)
