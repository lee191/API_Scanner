# Repository Guidelines

## 프로젝트 구조 및 모듈 구성
- `main.py`는 프록시 캡처, JS 분석, 취약점 스캔, 리포트를 통합하는 CLI 진입점입니다.
- `src/analyzer`, `src/crawler`, `src/scanner`, `src/proxy`, `src/reporter`, `src/utils`는 파이프라인 단계별 모듈을 제공하므로 새 기능은 가장 연관성 높은 패키지에 배치하세요.
- 실행 기본값은 `config/config.yaml`에서 관리하고, 개인 환경은 `.gitignore`에 포함된 `config/config.local.yaml`과 같은 파일로 분리합니다.
- `test-app/`에는 취약한 레퍼런스 앱이, `test-scripts/`에는 OS별 통합 테스트 스크립트가 저장됩니다.
- `output/`은 생성된 리포트가 모이는 위치이므로 커밋 전에 비우고, 자동화 테스트 코드는 `tests/` 하위에 정리하세요.

## 빌드 · 테스트 · 개발 명령어
- 가상환경을 만든 뒤(`python -m venv venv` → 활성화) `pip install -r requirements.txt`로 의존성을 설치합니다.
- 샘플 환경은 `./docker-run.sh` 또는 `test-scripts/run-test.sh`로 기동하며, Windows에서는 대응되는 `.bat` 스크립트를 사용합니다.
- 엔드포인트 탐지는 `python main.py analyze test-app/static --base-url http://localhost:5000 --recursive`로 수행합니다.
- 전체 파이프라인은 `python main.py full-scan <target-url> --js-path <static-dir> --scan-vulns --output output` 명령으로 실행합니다.
- 통합 테스트 후에는 `docker-stop.sh` 혹은 `stop-test-app.bat`으로 컨테이너를 종료하세요.

## 코딩 스타일 및 네이밍 규칙
- PEP 8과 4칸 들여쓰기, 가능하면 100자 이하 라인 길이를 유지합니다.
- 함수·변수는 `snake_case`, 클래스는 `PascalCase`, 상수는 `UPPER_SNAKE_CASE`로 작성합니다.
- 공유 스키마는 타입 힌트와 `pydantic` 모델로 정의하고, CLI 확장은 `click` 데코레이터로 노출합니다.
- 운영 코드에서는 표준 `logging`을 사용하고 임시 `print` 문은 제거합니다.

## 테스트 가이드라인
- 단위 테스트는 `tests/test_<module>.py` 형식을 따르고, 공통 픽스처는 필요 시 `tests/conftest.py`에 배치하세요.
- PR 전 `pytest -q`를 실행하고(미설치 시 `pip install pytest`), 실행 결과를 PR 설명에 기록합니다.
- 통합 검증은 `test-scripts/run-test.sh` 또는 `test-scripts\run-test.bat`으로 진행하며 HTML·JSON·Markdown 산출물이 `output/`에 있는지 확인합니다.
- 수동 테스트 흐름이나 데이터 의존성이 바뀌면 `TESTING.md`를 업데이트하세요.

## 커밋 및 풀 리퀘스트 안내
- 커밋 메시지는 `<type>: <imperative summary>` 예) `feat: add rate limit detector` 형식을 유지하고, 변경 사항은 한 주제로 집중합니다.
- 커밋 본문에는 영향을 받는 모듈·설정, 추후 작업 메모를 간단히 정리하세요.
- 풀 리퀘스트에는 개요, 관련 이슈 링크, 실행한 명령 체크리스트(`pytest`, 통합 스크립트, 수동 스캔 등)를 포함합니다.
- 리포트 스크린샷이나 정제된 결과를 첨부하되, `output/` 산출물은 커밋에서 제외하세요.

## 보안 및 설정 팁
- 실제 API 키·비밀·실환경 리포트는 절대 커밋하지 말고, 푸시 전에 `output/`을 비우세요.
- 로컬 비밀은 무시 목록에 포함된 설정 파일로 관리하고, 중요한 기본값은 `config/config.yaml`과 동기화하세요.
- 새로운 취약점 검사를 추가하면 `test-app/` 시드 데이터를 갱신하고 README·TESTING에 플래그와 사용법을 기록해 재현성을 유지하세요.
