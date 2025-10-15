"""
AI 비교 시스템 테스트 스크립트

이 스크립트는 비교 시스템이 제대로 작동하는지 테스트합니다.
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)


def test_imports():
    """필요한 모듈 임포트 테스트"""
    print(f"\n{Fore.CYAN}[1/5] 모듈 임포트 테스트...{Style.RESET_ALL}")
    
    try:
        from compare_ai_accuracy import AccuracyComparator
        print(f"{Fore.GREEN}  ✓ compare_ai_accuracy 임포트 성공{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}  ✗ compare_ai_accuracy 임포트 실패: {e}{Style.RESET_ALL}")
        return False
    
    try:
        import sqlite3
        import json
        from datetime import datetime
        print(f"{Fore.GREEN}  ✓ 필수 라이브러리 임포트 성공{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}  ✗ 필수 라이브러리 임포트 실패: {e}{Style.RESET_ALL}")
        return False
    
    return True


def test_ground_truth():
    """Ground Truth 파일 존재 확인"""
    print(f"\n{Fore.CYAN}[2/5] Ground Truth 파일 확인...{Style.RESET_ALL}")
    
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    gt_path = project_root / "ground_truth.json"
    
    if not gt_path.exists():
        print(f"{Fore.YELLOW}  ! ground_truth.json 없음{Style.RESET_ALL}")
        
        # Try to use complete version
        complete_path = project_root / "ground_truth_complete.json"
        if complete_path.exists():
            print(f"{Fore.CYAN}  → ground_truth_complete.json 사용 가능{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}  ✗ Ground Truth 파일을 찾을 수 없습니다{Style.RESET_ALL}")
            return False
    
    print(f"{Fore.GREEN}  ✓ ground_truth.json 존재{Style.RESET_ALL}")
    
    # Validate JSON
    try:
        import json
        with open(gt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'endpoints' in data:
            print(f"{Fore.GREEN}  ✓ Ground Truth 형식 유효 ({len(data['endpoints'])}개 엔드포인트){Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}  ✗ Ground Truth 형식 오류 (endpoints 키 없음){Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}  ✗ Ground Truth 파싱 실패: {e}{Style.RESET_ALL}")
        return False


def test_directories():
    """필요한 디렉토리 확인"""
    print(f"\n{Fore.CYAN}[3/5] 디렉토리 구조 확인...{Style.RESET_ALL}")
    
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    required_dirs = ['data', 'output']
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            print(f"{Fore.YELLOW}  ! {dir_name}/ 디렉토리 생성{Style.RESET_ALL}")
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            print(f"{Fore.GREEN}  ✓ {dir_name}/ 존재{Style.RESET_ALL}")
    
    return True


def test_comparator_init():
    """AccuracyComparator 초기화 테스트"""
    print(f"\n{Fore.CYAN}[4/5] AccuracyComparator 초기화 테스트...{Style.RESET_ALL}")
    
    try:
        from compare_ai_accuracy import AccuracyComparator
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent
        
        # Use complete version if available
        gt_path = project_root / "ground_truth.json"
        if not gt_path.exists():
            gt_path = project_root / "ground_truth_complete.json"
        
        comparator = AccuracyComparator(str(gt_path))
        print(f"{Fore.GREEN}  ✓ AccuracyComparator 초기화 성공{Style.RESET_ALL}")
        
        # Check ground truth loaded
        print(f"{Fore.GREEN}  ✓ Ground Truth 로드: {len(comparator.gt_endpoints)}개 엔드포인트{Style.RESET_ALL}")
        
        return True
    except Exception as e:
        print(f"{Fore.RED}  ✗ AccuracyComparator 초기화 실패: {e}{Style.RESET_ALL}")
        return False


def test_metric_calculation():
    """메트릭 계산 함수 테스트"""
    print(f"\n{Fore.CYAN}[5/5] 메트릭 계산 함수 테스트...{Style.RESET_ALL}")
    
    try:
        from compare_ai_accuracy import AccuracyComparator
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent
        gt_path = project_root / "ground_truth.json"
        if not gt_path.exists():
            gt_path = project_root / "ground_truth_complete.json"
        
        comparator = AccuracyComparator(str(gt_path))
        
        # Create dummy scan results
        dummy_endpoints = set([
            ('GET', '/api/v1/users'),
            ('POST', '/api/v1/auth/login'),
            ('GET', '/api/fake/endpoint')  # False positive
        ])
        
        metrics = comparator.calculate_metrics(dummy_endpoints)
        
        print(f"{Fore.GREEN}  ✓ 메트릭 계산 성공{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    - Precision: {metrics['precision']:.2%}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    - Recall: {metrics['recall']:.2%}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    - F1-Score: {metrics['f1_score']:.2%}{Style.RESET_ALL}")
        
        return True
    except Exception as e:
        print(f"{Fore.RED}  ✗ 메트릭 계산 실패: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'AI 비교 시스템 테스트'.center(60)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    tests = [
        ("모듈 임포트", test_imports),
        ("Ground Truth", test_ground_truth),
        ("디렉토리", test_directories),
        ("Comparator 초기화", test_comparator_init),
        ("메트릭 계산", test_metric_calculation),
    ]
    
    results = []
    
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'테스트 결과'.center(60)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}" if result else f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
        print(f"  {status}  {name}")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    if passed == total:
        print(f"{Fore.GREEN}✓ 모든 테스트 통과! ({passed}/{total}){Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}다음 단계:{Style.RESET_ALL}")
        print(f"  1. 프로젝트 루트로 이동: {Fore.YELLOW}cd ..{Style.RESET_ALL}")
        print(f"  2. 테스트 앱 실행: {Fore.YELLOW}start-test-app.bat{Style.RESET_ALL}")
        print(f"  3. 비교 실행: {Fore.YELLOW}cd comparison && run-comparison.bat{Style.RESET_ALL}")
        print(f"  또는 직접: {Fore.YELLOW}python comparison/compare_ai_accuracy.py{Style.RESET_ALL}\n")
        return 0
    else:
        print(f"{Fore.RED}✗ 일부 테스트 실패 ({passed}/{total}){Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}실패한 테스트를 확인하고 수정해주세요.{Style.RESET_ALL}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
