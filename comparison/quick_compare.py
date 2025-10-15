"""
간단한 정확도 비교 예제

이 스크립트는 AI 사용/미사용 스캔의 정확도를 빠르게 비교합니다.
"""

from compare_ai_accuracy import AccuracyComparator
from colorama import init, Fore, Style

init(autoreset=True)


def quick_comparison():
    """빠른 비교 실행"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}빠른 정확도 비교{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    # Paths relative to project root
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    
    # 기존 스캔 결과 사용
    comparator = AccuracyComparator(
        ground_truth_path=str(project_root / "ground_truth.json"),
        db_with_ai=str(project_root / "data" / "scanner_with_ai.db"),
        db_without_ai=str(project_root / "data" / "scanner_without_ai.db")
    )
    
    # 결과 비교
    comparison = comparator.compare_results()
    
    # 리포트 출력
    comparator.print_comparison_report(comparison)
    
    # JSON 저장
    output_file = comparator.export_comparison(comparison)
    
    print(f"{Fore.GREEN}✓ 완료!{Style.RESET_ALL}")
    print(f"리포트: {output_file}\n")


def show_metrics_only():
    """메트릭만 간단히 출력"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}정확도 메트릭 요약{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    
    comparator = AccuracyComparator(str(project_root / "ground_truth.json"))
    
    # AI 사용 결과
    endpoints_with_ai = comparator._load_scan_results(str(project_root / "data" / "scanner_with_ai.db"))
    metrics_ai = comparator.calculate_metrics(endpoints_with_ai)
    
    # AI 미사용 결과
    endpoints_without_ai = comparator._load_scan_results(str(project_root / "data" / "scanner_without_ai.db"))
    metrics_no_ai = comparator.calculate_metrics(endpoints_without_ai)
    
    # 출력
    print(f"{Fore.YELLOW}AI 미사용:{Style.RESET_ALL}")
    print(f"  Precision: {Fore.CYAN}{metrics_no_ai['precision']:.2%}{Style.RESET_ALL}")
    print(f"  Recall:    {Fore.CYAN}{metrics_no_ai['recall']:.2%}{Style.RESET_ALL}")
    print(f"  F1-Score:  {Fore.CYAN}{metrics_no_ai['f1_score']:.2%}{Style.RESET_ALL}")
    print()
    
    print(f"{Fore.YELLOW}AI 사용:{Style.RESET_ALL}")
    print(f"  Precision: {Fore.GREEN}{metrics_ai['precision']:.2%}{Style.RESET_ALL}")
    print(f"  Recall:    {Fore.GREEN}{metrics_ai['recall']:.2%}{Style.RESET_ALL}")
    print(f"  F1-Score:  {Fore.GREEN}{metrics_ai['f1_score']:.2%}{Style.RESET_ALL}")
    print()
    
    # 개선도
    improvement = metrics_ai['f1_score'] - metrics_no_ai['f1_score']
    if improvement > 0:
        print(f"{Fore.GREEN}✓ AI 분석으로 {improvement:.2%}p 개선{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}✗ AI 분석으로 {abs(improvement):.2%}p 하락{Style.RESET_ALL}\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--metrics-only':
        show_metrics_only()
    else:
        quick_comparison()
