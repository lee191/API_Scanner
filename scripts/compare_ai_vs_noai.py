#!/usr/bin/env python3
"""
AI vs Non-AI 엔드포인트 탐지 비교 스크립트

AI를 사용한 탐지와 사용하지 않은 탐지를 비교하여 정확도를 측정합니다.
"""

import sys
import json
from pathlib import Path
from typing import List, Set, Tuple, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.js_analyzer import JSAnalyzer
from src.utils.models import APIEndpoint


def load_ground_truth(path: str) -> Set[Tuple[str, str]]:
    """Ground truth 로드 및 정규화"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    endpoints = set()
    for ep in data['endpoints']:
        method = ep['method']
        url = ep['url']
        # URL 정규화
        url = url.rstrip('/').lower()
        endpoints.add((method, url))

    return endpoints


def analyze_js_files(js_path: str, base_url: str, use_ai: bool) -> Set[Tuple[str, str]]:
    """JavaScript 파일 분석 (AI 사용/미사용)"""
    analyzer = JSAnalyzer(use_ai=use_ai)
    endpoints = set()

    js_dir = Path(js_path)
    js_files = list(js_dir.glob('*.js'))

    print(f"\n{'[AI]' if use_ai else '[Regex]'} 분석 중... (파일 {len(js_files)}개)")

    for js_file in js_files:
        file_endpoints = analyzer.analyze_file(str(js_file), base_url)

        for ep in file_endpoints:
            method = ep.method.value if hasattr(ep.method, 'value') else str(ep.method)
            url = ep.url

            # URL 정규화 (base URL 제거)
            if url.startswith(base_url):
                url = url.replace(base_url, '')

            url = url.rstrip('/').lower()

            # API URL만 필터링
            if '/api/' in url or '/internal/' in url:
                endpoints.add((method, url))

    return endpoints


def calculate_metrics(detected: Set, ground_truth: Set) -> Dict:
    """정확도 메트릭 계산"""
    tp = detected & ground_truth  # True Positives
    fp = detected - ground_truth  # False Positives
    fn = ground_truth - detected  # False Negatives

    precision = len(tp) / len(detected) if detected else 0
    recall = len(tp) / len(ground_truth) if ground_truth else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'tp': len(tp),
        'fp': len(fp),
        'fn': len(fn),
        'total_detected': len(detected),
        'total_ground_truth': len(ground_truth),
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'tp_list': sorted(list(tp)),
        'fp_list': sorted(list(fp)),
        'fn_list': sorted(list(fn))
    }


def print_comparison_report(ai_metrics: Dict, noai_metrics: Dict):
    """비교 리포트 출력"""

    print("\n" + "=" * 80)
    print("AI vs Non-AI 엔드포인트 탐지 비교".center(80))
    print("=" * 80 + "\n")

    # 요약 테이블
    print("=" * 80)
    print("요약 비교".center(80))
    print("=" * 80)
    print(f"{'지표':<30} {'AI 사용':>20} {'AI 미사용':>20}")
    print("-" * 80)
    print(f"{'탐지된 엔드포인트':<30} {ai_metrics['total_detected']:>20} {noai_metrics['total_detected']:>20}")
    print(f"{'True Positives (TP)':<30} {ai_metrics['tp']:>20} {noai_metrics['tp']:>20}")
    print(f"{'False Positives (FP)':<30} {ai_metrics['fp']:>20} {noai_metrics['fp']:>20}")
    print(f"{'False Negatives (FN)':<30} {ai_metrics['fn']:>20} {noai_metrics['fn']:>20}")
    print()
    print(f"{'Precision (정밀도)':<30} {ai_metrics['precision']:>19.2%} {noai_metrics['precision']:>19.2%}")
    print(f"{'Recall (재현율)':<30} {ai_metrics['recall']:>19.2%} {noai_metrics['recall']:>19.2%}")
    print(f"{'F1-Score':<30} {ai_metrics['f1_score']:>19.2%} {noai_metrics['f1_score']:>19.2%}")
    print("=" * 80)

    # 성능 개선 분석
    print("\n" + "=" * 80)
    print("AI 성능 개선 분석".center(80))
    print("=" * 80)

    precision_improve = ((ai_metrics['precision'] - noai_metrics['precision']) / noai_metrics['precision'] * 100) if noai_metrics['precision'] > 0 else 0
    recall_improve = ((ai_metrics['recall'] - noai_metrics['recall']) / noai_metrics['recall'] * 100) if noai_metrics['recall'] > 0 else 0
    f1_improve = ((ai_metrics['f1_score'] - noai_metrics['f1_score']) / noai_metrics['f1_score'] * 100) if noai_metrics['f1_score'] > 0 else 0

    print(f"Precision 개선:  {precision_improve:+.1f}% ({noai_metrics['precision']:.1%} → {ai_metrics['precision']:.1%})")
    print(f"Recall 개선:     {recall_improve:+.1f}% ({noai_metrics['recall']:.1%} → {ai_metrics['recall']:.1%})")
    print(f"F1-Score 개선:   {f1_improve:+.1f}% ({noai_metrics['f1_score']:.1%} → {ai_metrics['f1_score']:.1%})")

    # AI가 추가로 찾은 엔드포인트
    ai_only = set(ai_metrics['tp_list']) - set(noai_metrics['tp_list'])
    if ai_only:
        print(f"\n[AI 전용 탐지] AI만 찾은 엔드포인트 ({len(ai_only)}개):")
        for method, url in sorted(ai_only):
            print(f"  {method:6} {url}")

    # Non-AI가 추가로 찾은 엔드포인트 (AI가 놓친 것)
    noai_only = set(noai_metrics['tp_list']) - set(ai_metrics['tp_list'])
    if noai_only:
        print(f"\n[Regex 전용 탐지] AI가 놓쳤지만 Regex가 찾은 엔드포인트 ({len(noai_only)}개):")
        for method, url in sorted(noai_only):
            print(f"  {method:6} {url}")

    # 둘 다 놓친 엔드포인트
    both_missed = set(ai_metrics['fn_list']) & set(noai_metrics['fn_list'])
    if both_missed:
        print(f"\n[공통 미탐지] 둘 다 찾지 못한 엔드포인트 ({len(both_missed)}개):")
        for method, url in sorted(both_missed):
            print(f"  {method:6} {url}")

    print("\n" + "=" * 80)

    # 결론
    print("\n결론:")
    if ai_metrics['f1_score'] > noai_metrics['f1_score']:
        improvement = (ai_metrics['f1_score'] - noai_metrics['f1_score']) * 100
        print(f"✅ AI 사용이 F1-Score를 {improvement:.1f}%p 향상시켰습니다.")
    else:
        print("⚠️ AI 사용이 큰 개선을 보이지 않았습니다.")

    print(f"   - AI 추가 발견: {len(ai_only)}개")
    print(f"   - AI 미발견: {len(noai_only)}개")
    print(f"   - 공통 미탐지: {len(both_missed)}개")
    print("=" * 80 + "\n")


def export_json_report(ai_metrics: Dict, noai_metrics: Dict, output_path: str):
    """JSON 리포트 저장"""
    report = {
        'ai': {
            'total_detected': ai_metrics['total_detected'],
            'true_positives': ai_metrics['tp'],
            'false_positives': ai_metrics['fp'],
            'false_negatives': ai_metrics['fn'],
            'precision': ai_metrics['precision'],
            'recall': ai_metrics['recall'],
            'f1_score': ai_metrics['f1_score']
        },
        'no_ai': {
            'total_detected': noai_metrics['total_detected'],
            'true_positives': noai_metrics['tp'],
            'false_positives': noai_metrics['fp'],
            'false_negatives': noai_metrics['fn'],
            'precision': noai_metrics['precision'],
            'recall': noai_metrics['recall'],
            'f1_score': noai_metrics['f1_score']
        },
        'comparison': {
            'precision_improvement': ai_metrics['precision'] - noai_metrics['precision'],
            'recall_improvement': ai_metrics['recall'] - noai_metrics['recall'],
            'f1_improvement': ai_metrics['f1_score'] - noai_metrics['f1_score']
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[+] JSON 리포트 저장: {output_path}")


def main():
    """메인 함수"""

    print("\n" + "=" * 80)
    print("AI vs Non-AI 엔드포인트 탐지 비교 도구".center(80))
    print("=" * 80 + "\n")

    # 경로 설정
    ground_truth_path = "ground_truth.json"
    js_path = "test-app/static"
    base_url = "http://localhost:5000"
    output_json = "docs/analysis/ai_vs_noai_comparison.json"

    # Ground truth 로드
    print(f"[1/4] Ground Truth 로드: {ground_truth_path}")
    ground_truth = load_ground_truth(ground_truth_path)
    print(f"      총 {len(ground_truth)}개 실제 API 엔드포인트")

    # AI 없이 분석
    print(f"\n[2/4] Regex 기반 분석 (AI 미사용)")
    noai_detected = analyze_js_files(js_path, base_url, use_ai=False)
    print(f"      탐지: {len(noai_detected)}개")

    # AI 사용하여 분석
    print(f"\n[3/4] AI 기반 분석 (OpenAI GPT)")
    ai_detected = analyze_js_files(js_path, base_url, use_ai=True)
    print(f"      탐지: {len(ai_detected)}개")

    # 메트릭 계산
    print(f"\n[4/4] 정확도 메트릭 계산 중...")
    ai_metrics = calculate_metrics(ai_detected, ground_truth)
    noai_metrics = calculate_metrics(noai_detected, ground_truth)

    # 리포트 출력
    print_comparison_report(ai_metrics, noai_metrics)

    # JSON 저장
    export_json_report(ai_metrics, noai_metrics, output_json)

    return 0


if __name__ == '__main__':
    sys.exit(main())
