"""
AI 사용/미사용 스캔 결과 비교 및 정확도 분석 스크립트

이 스크립트는:
1. AI 분석을 사용한 스캔 실행
2. AI 분석을 사용하지 않은 스캔 실행
3. 두 결과를 Ground Truth와 비교하여 정확도 계산
4. 상세한 비교 리포트 생성

결과는 JSON 파일에서 읽어와 비교합니다.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from datetime import datetime
from colorama import init, Fore, Style
import subprocess
import shutil

init(autoreset=True)


class AccuracyComparator:
    """AI 사용/미사용 스캔 결과 비교 및 정확도 분석"""

    def __init__(self, ground_truth_path: str, output_dir: str = "output/accuracy_comparison",
                 json_with_ai: str = None, json_without_ai: str = None):
        """
        Initialize comparator.

        Args:
            ground_truth_path: Ground truth JSON 파일 경로
            output_dir: 출력 디렉토리
            json_with_ai: AI 사용 스캔 JSON 결과 경로 (선택사항)
            json_without_ai: AI 미사용 스캔 JSON 결과 경로 (선택사항)
        """
        self.ground_truth_path = ground_truth_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load ground truth
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            self.ground_truth_data = json.load(f)
        
        self.gt_endpoints = self._normalize_ground_truth()
        
        # JSON result paths (relative to project root)
        self.json_with_ai = json_with_ai or str(Path(__file__).parent.parent / "output" / "AI_사용" / "scan_results.json")
        self.json_without_ai = json_without_ai or str(Path(__file__).parent.parent / "output" / "AI_미사용" / "scan_results.json")
        
    def _normalize_ground_truth(self) -> Set[Tuple[str, str]]:
        """Ground truth를 (method, url) 튜플 집합으로 정규화"""
        normalized = set()
        for ep in self.ground_truth_data['endpoints']:
            method = ep['method']
            url = self._normalize_url(ep['url'])
            normalized.add((method, url))
        return normalized

    def _normalize_url(self, url: str) -> str:
        """URL 정규화"""
        # Remove base URL
        if url.startswith('http://localhost:5000'):
            url = url.replace('http://localhost:5000', '')
        elif url.startswith('http://'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url = parsed.path
        
        # Normalize
        url = url.rstrip('/').lower()
        
        return url

    def _load_scan_results(self, json_path: str) -> Set[Tuple[str, str]]:
        """JSON 파일에서 스캔 결과 로드"""
        if not Path(json_path).exists():
            print(f"{Fore.YELLOW}[!] JSON 파일을 찾을 수 없음: {json_path}{Style.RESET_ALL}")
            return set()

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"{Fore.RED}[!] JSON 파일 읽기 실패: {json_path} - {e}{Style.RESET_ALL}")
            return set()

        scanned = set()
        
        # Load endpoints from JSON
        endpoints = data.get('endpoints', [])
        for ep in endpoints:
            method = ep.get('method', 'GET')
            url = ep.get('url', '')
            if url:
                url = self._normalize_url(url)
                scanned.add((method, url))

        return scanned

    def calculate_metrics(self, scanned_endpoints: Set[Tuple[str, str]]) -> Dict:
        """정확도 메트릭 계산"""
        # True Positives: 스캔으로 찾았고 실제로도 존재
        true_positives = scanned_endpoints & self.gt_endpoints

        # False Positives: 스캔으로 찾았지만 실제로는 없음
        false_positives = scanned_endpoints - self.gt_endpoints

        # False Negatives: 실제로 존재하지만 스캔으로 찾지 못함
        false_negatives = self.gt_endpoints - scanned_endpoints

        tp_count = len(true_positives)
        fp_count = len(false_positives)
        fn_count = len(false_negatives)

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'true_positives': tp_count,
            'false_positives': fp_count,
            'false_negatives': fn_count,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'total_ground_truth': len(self.gt_endpoints),
            'total_detected': len(scanned_endpoints),
            'tp_list': sorted(list(true_positives)),
            'fp_list': sorted(list(false_positives)),
            'fn_list': sorted(list(false_negatives))
        }

    def run_scan(self, target: str, js_path: str, use_ai: bool) -> str:
        """스캔 실행"""
        scan_type = "AI 사용" if use_ai else "AI 미사용"
        output_dir = str(Path(__file__).parent.parent / 'output' / scan_type.replace(" ", "_"))
        json_path = Path(output_dir) / "scan_results.json"
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] {scan_type} 스캔 시작...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

        # Clean existing output directory
        if Path(output_dir).exists():
            backup_dir = f"{output_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(output_dir, backup_dir)
            print(f"{Fore.YELLOW}[*] 기존 결과 백업: {backup_dir}{Style.RESET_ALL}")

        # Set environment variable for AI
        env = os.environ.copy()
        env['AI_ANALYSIS_ENABLED'] = 'true' if use_ai else 'false'
        
        # Run scan
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / 'main.py'),
            'full-scan',
            target,
            '--js-path', js_path,
            '--no-scan-vulns',  # Skip vulnerability scanning for speed
            '--output', output_dir
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print(f"{Fore.RED}[!] 스캔 실패:{Style.RESET_ALL}")
                print(result.stderr)
                return str(json_path)
                
            print(f"{Fore.GREEN}[+] {scan_type} 스캔 완료{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[+] 결과 저장: {json_path}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] 스캔 실행 중 오류: {e}{Style.RESET_ALL}")
        
        return str(json_path)

    def compare_results(self) -> Dict:
        """AI 사용/미사용 결과 비교"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] 스캔 결과 비교 중...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

        # Load results from JSON files
        endpoints_with_ai = self._load_scan_results(self.json_with_ai)
        endpoints_without_ai = self._load_scan_results(self.json_without_ai)

        # Calculate metrics
        metrics_with_ai = self.calculate_metrics(endpoints_with_ai)
        metrics_without_ai = self.calculate_metrics(endpoints_without_ai)

        # Compare
        comparison = {
            'with_ai': metrics_with_ai,
            'without_ai': metrics_without_ai,
            'improvement': {
                'precision': metrics_with_ai['precision'] - metrics_without_ai['precision'],
                'recall': metrics_with_ai['recall'] - metrics_without_ai['recall'],
                'f1_score': metrics_with_ai['f1_score'] - metrics_without_ai['f1_score'],
                'detected_endpoints': metrics_with_ai['total_detected'] - metrics_without_ai['total_detected'],
                'true_positives': metrics_with_ai['true_positives'] - metrics_without_ai['true_positives'],
            },
            'ai_only_found': sorted(list(endpoints_with_ai - endpoints_without_ai - (endpoints_with_ai - self.gt_endpoints))),
            'non_ai_only_found': sorted(list(endpoints_without_ai - endpoints_with_ai - (endpoints_without_ai - self.gt_endpoints))),
            'timestamp': datetime.now().isoformat()
        }

        return comparison

    def print_comparison_report(self, comparison: Dict):
        """비교 리포트 출력"""
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'AI 사용/미사용 스캔 결과 비교 리포트'.center(100)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

        # Summary table
        print(f"{Fore.YELLOW}┌{'─'*98}┐{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}│ {'지표':<30} │ {'AI 미사용':<20} │ {'AI 사용':<20} │ {'개선':<20} │{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}├{'─'*98}┤{Style.RESET_ALL}")
        
        metrics_ai = comparison['with_ai']
        metrics_no_ai = comparison['without_ai']
        improvement = comparison['improvement']

        # Total detected
        print(f"│ {'탐지된 총 엔드포인트':<30} │ {metrics_no_ai['total_detected']:<20} │ "
              f"{metrics_ai['total_detected']:<20} │ "
              f"{self._format_improvement(improvement['detected_endpoints']):<20} │")
        
        # True Positives
        print(f"│ {'정확히 탐지 (TP)':<30} │ {metrics_no_ai['true_positives']:<20} │ "
              f"{metrics_ai['true_positives']:<20} │ "
              f"{self._format_improvement(improvement['true_positives']):<20} │")
        
        # False Positives
        print(f"│ {'오탐지 (FP)':<30} │ {metrics_no_ai['false_positives']:<20} │ "
              f"{metrics_ai['false_positives']:<20} │ "
              f"{self._format_improvement(metrics_no_ai['false_positives'] - metrics_ai['false_positives'], inverse=True):<20} │")
        
        # False Negatives
        print(f"│ {'미탐지 (FN)':<30} │ {metrics_no_ai['false_negatives']:<20} │ "
              f"{metrics_ai['false_negatives']:<20} │ "
              f"{self._format_improvement(metrics_no_ai['false_negatives'] - metrics_ai['false_negatives'], inverse=True):<20} │")
        
        print(f"{Fore.YELLOW}├{'─'*98}┤{Style.RESET_ALL}")
        
        # Precision
        print(f"│ {'Precision (정밀도)':<30} │ {metrics_no_ai['precision']:.2%}{'':>14} │ "
              f"{metrics_ai['precision']:.2%}{'':>14} │ "
              f"{self._format_improvement(improvement['precision'], percentage=True):<20} │")
        
        # Recall
        print(f"│ {'Recall (재현율)':<30} │ {metrics_no_ai['recall']:.2%}{'':>14} │ "
              f"{metrics_ai['recall']:.2%}{'':>14} │ "
              f"{self._format_improvement(improvement['recall'], percentage=True):<20} │")
        
        # F1-Score
        print(f"│ {'F1-Score':<30} │ {metrics_no_ai['f1_score']:.2%}{'':>14} │ "
              f"{metrics_ai['f1_score']:.2%}{'':>14} │ "
              f"{self._format_improvement(improvement['f1_score'], percentage=True):<20} │")
        
        print(f"{Fore.YELLOW}└{'─'*98}┘{Style.RESET_ALL}\n")

        # Detailed analysis
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}상세 분석{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

        # AI only found (correct detections)
        if comparison['ai_only_found']:
            print(f"{Fore.GREEN}[+] AI만 탐지한 엔드포인트 (실제 존재) - {len(comparison['ai_only_found'])}개:{Style.RESET_ALL}")
            for method, url in comparison['ai_only_found']:
                print(f"    {method:6} {url}")
            print()

        # Non-AI only found (correct detections)
        if comparison['non_ai_only_found']:
            print(f"{Fore.YELLOW}[*] 기본 분석만으로 탐지한 엔드포인트 (실제 존재) - {len(comparison['non_ai_only_found'])}개:{Style.RESET_ALL}")
            for method, url in comparison['non_ai_only_found']:
                print(f"    {method:6} {url}")
            print()

        # AI false positives
        ai_fp_only = set(metrics_ai['fp_list']) - set(metrics_no_ai['fp_list'])
        if ai_fp_only:
            print(f"{Fore.RED}[!] AI 분석의 고유 오탐지 - {len(ai_fp_only)}개:{Style.RESET_ALL}")
            for method, url in sorted(ai_fp_only):
                print(f"    {method:6} {url}")
            print()

        # Non-AI false positives
        no_ai_fp_only = set(metrics_no_ai['fp_list']) - set(metrics_ai['fp_list'])
        if no_ai_fp_only:
            print(f"{Fore.RED}[!] 기본 분석의 고유 오탐지 - {len(no_ai_fp_only)}개:{Style.RESET_ALL}")
            for method, url in sorted(no_ai_fp_only):
                print(f"    {method:6} {url}")
            print()

        # Performance grade
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}종합 평가{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
        
        ai_grade = self._get_grade(metrics_ai['f1_score'])
        no_ai_grade = self._get_grade(metrics_no_ai['f1_score'])
        
        print(f"AI 미사용: {no_ai_grade['color']}{no_ai_grade['grade']} (F1-Score: {metrics_no_ai['f1_score']:.2%}){Style.RESET_ALL}")
        print(f"AI 사용:   {ai_grade['color']}{ai_grade['grade']} (F1-Score: {metrics_ai['f1_score']:.2%}){Style.RESET_ALL}")
        
        if improvement['f1_score'] > 0:
            print(f"\n{Fore.GREEN}✓ AI 분석으로 {improvement['f1_score']:.2%}p 개선{Style.RESET_ALL}")
        elif improvement['f1_score'] < 0:
            print(f"\n{Fore.RED}✗ AI 분석으로 {abs(improvement['f1_score']):.2%}p 하락{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}= 동일한 성능{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

    def _format_improvement(self, value: float, percentage: bool = False, inverse: bool = False) -> str:
        """개선 수치 포맷팅"""
        if percentage:
            formatted = f"{value:+.2%}p"
        else:
            formatted = f"{value:+.0f}"
        
        # Inverse: 값이 감소하는 것이 개선 (FP, FN)
        if inverse:
            value = -value
        
        if value > 0:
            return f"{Fore.GREEN}{formatted}{Style.RESET_ALL}"
        elif value < 0:
            return f"{Fore.RED}{formatted}{Style.RESET_ALL}"
        else:
            return f"{Fore.YELLOW}{formatted}{Style.RESET_ALL}"

    def _get_grade(self, f1_score: float) -> Dict:
        """F1-Score에 따른 등급 반환"""
        if f1_score >= 0.95:
            return {'grade': 'S (Excellent)', 'color': Fore.GREEN}
        elif f1_score >= 0.90:
            return {'grade': 'A (Very Good)', 'color': Fore.GREEN}
        elif f1_score >= 0.80:
            return {'grade': 'B (Good)', 'color': Fore.CYAN}
        elif f1_score >= 0.70:
            return {'grade': 'C (Fair)', 'color': Fore.YELLOW}
        elif f1_score >= 0.60:
            return {'grade': 'D (Poor)', 'color': Fore.YELLOW}
        else:
            return {'grade': 'F (Very Poor)', 'color': Fore.RED}

    def export_comparison(self, comparison: Dict):
        """비교 결과를 JSON 파일로 저장"""
        output_file = self.output_dir / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert tuples to dicts for JSON serialization
        comparison_export = {
            'with_ai': {
                **comparison['with_ai'],
                'tp_list': [{'method': m, 'url': u} for m, u in comparison['with_ai']['tp_list']],
                'fp_list': [{'method': m, 'url': u} for m, u in comparison['with_ai']['fp_list']],
                'fn_list': [{'method': m, 'url': u} for m, u in comparison['with_ai']['fn_list']],
            },
            'without_ai': {
                **comparison['without_ai'],
                'tp_list': [{'method': m, 'url': u} for m, u in comparison['without_ai']['tp_list']],
                'fp_list': [{'method': m, 'url': u} for m, u in comparison['without_ai']['fp_list']],
                'fn_list': [{'method': m, 'url': u} for m, u in comparison['without_ai']['fn_list']],
            },
            'improvement': comparison['improvement'],
            'ai_only_found': [{'method': m, 'url': u} for m, u in comparison['ai_only_found']],
            'non_ai_only_found': [{'method': m, 'url': u} for m, u in comparison['non_ai_only_found']],
            'timestamp': comparison['timestamp']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_export, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}[+] 비교 리포트 저장: {output_file}{Style.RESET_ALL}\n")
        
        return output_file


def main():
    """메인 함수"""
    print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'AI 사용/미사용 스캔 비교 및 정확도 분석'.center(100)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

    # Configuration (relative to project root)
    project_root = Path(__file__).parent.parent
    target = "http://localhost:5000"
    js_path = str(project_root / "test-app" / "static")
    ground_truth = str(project_root / "ground_truth.json")

    # Check prerequisites
    if not Path(ground_truth).exists():
        print(f"{Fore.RED}[!] Ground truth 파일을 찾을 수 없습니다: {ground_truth}{Style.RESET_ALL}")
        return 1

    if not Path(js_path).exists():
        print(f"{Fore.RED}[!] JavaScript 경로를 찾을 수 없습니다: {js_path}{Style.RESET_ALL}")
        return 1

    # Create comparator
    comparator = AccuracyComparator(ground_truth)

    # Option: Run new scans or use existing databases
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--skip-scan':
        print(f"{Fore.YELLOW}[*] 기존 스캔 결과 사용 (새 스캔 건너뛰기){Style.RESET_ALL}\n")
    else:
        # Run scan without AI
        comparator.run_scan(target, js_path, use_ai=False)
        
        # Run scan with AI
        comparator.run_scan(target, js_path, use_ai=True)

    # Compare results
    comparison = comparator.compare_results()
    
    # Print report
    comparator.print_comparison_report(comparison)
    
    # Export report
    comparator.export_comparison(comparison)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] 사용자에 의해 중단됨{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[!] 오류 발생: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
