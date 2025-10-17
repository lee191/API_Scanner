# 📦 API Scanner 설치 및 실행 가이드

## 목차
- [시스템 요구사항](#시스템-요구사항)
- [프로젝트 다운로드](#프로젝트-다운로드)
- [백엔드 설정](#백엔드-설정)
- [프론트엔드 설정](#프론트엔드-설정)
- [데이터베이스 초기화](#데이터베이스-초기화)
- [서버 실행](#서버-실행)
- [웹 UI 사용법](#웹-ui-사용법)
- [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 필수 소프트웨어
- **Python**: 3.8 이상 (권장: 3.10+)
- **Node.js**: 16.x 이상 (권장: 18.x+)
- **npm** 또는 **yarn**
- **Git**

### 운영체제
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, CentOS 8+)

### 하드웨어 권장 사양
- **RAM**: 최소 4GB (권장 8GB+)
- **저장공간**: 최소 2GB
- **인터넷 연결**: 필수 (AI 분석 사용 시)

---

## 프로젝트 다운로드

### 1. Git Clone

```bash
# HTTPS 방식
git clone https://github.com/lee191/API_Scanner.git

# SSH 방식 (Git 계정 설정 시)
git clone git@github.com:lee191/API_Scanner.git
```

### 2. 프로젝트 디렉토리 이동

```bash
cd API_Scanner
```

### 3. 프로젝트 구조 확인

```bash
# Windows
dir

# Linux/macOS
ls -la
```

**예상 출력:**
```
API_Scanner/
├── main.py                 # CLI 메인 엔트리
├── api_server.py          # Flask API 서버
├── requirements.txt       # Python 의존성
├── config/               # 설정 파일
├── src/                  # 소스 코드
├── web-ui/              # Next.js 프론트엔드
├── wordlists/           # 브루트포싱 워드리스트
└── test-app/            # 테스트용 Flask 앱
```

---

## 백엔드 설정

### 1. Python 가상환경 생성 (권장)

#### Windows
```powershell
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# PowerShell 실행 정책 오류 시
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Linux/macOS
```bash
# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 2. Python 패키지 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 설치 확인
pip list
```

**주요 패키지:**
- `flask`: API 서버
- `requests`: HTTP 클라이언트
- `beautifulsoup4`: HTML 파싱
- `openai`: AI 분석 (GPT-4o)
- `sqlalchemy`: 데이터베이스 ORM
- `colorama`: 터미널 색상
- `click`: CLI 프레임워크

### 3. OpenAI API 키 설정 (AI 분석 사용 시)

#### 환경변수 설정

**Windows (PowerShell):**
```powershell
# 임시 설정 (현재 세션만)
$env:OPENAI_API_KEY = "sk-your-api-key-here"

# 영구 설정
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-api-key-here', 'User')
```

**Linux/macOS (Bash):**
```bash
# 임시 설정
export OPENAI_API_KEY="sk-your-api-key-here"

# 영구 설정 (~/.bashrc 또는 ~/.zshrc에 추가)
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### 설정 파일 사용 (선택)

`config/config.yaml` 파일 생성:
```yaml
openai:
  api_key: "sk-your-api-key-here"
  model: "gpt-4o"
  max_tokens: 4000
```

---

## 프론트엔드 설정

### 1. Node.js 프로젝트 디렉토리 이동

```bash
cd web-ui
```

### 2. Node.js 패키지 설치

#### npm 사용
```bash
npm install
```

#### yarn 사용 (선택)
```bash
yarn install
```

### 3. 환경변수 설정 (선택)

`.env.local` 파일 생성:
```env
# API 서버 URL (개발 환경)
NEXT_PUBLIC_API_URL=http://localhost:5001

# 기타 설정
NEXT_PUBLIC_APP_NAME="API Scanner"
```

### 4. 빌드 테스트 (선택)

```bash
npm run build
```

---

## 데이터베이스 초기화

### 1. 프로젝트 루트 디렉토리로 이동

```bash
# web-ui 디렉토리에 있다면
cd ..
```

### 2. 데이터베이스 초기화 스크립트 실행

```bash
python setup_db.py
```

**예상 출력:**
```
[*] Initializing database...
[+] Database initialized successfully!
[+] Tables created:
  - projects
  - scans
  - endpoints
  - vulnerabilities
  - discovered_paths
```

### 3. 데이터베이스 확인

```bash
python check_db.py
```

---

## 서버 실행

### 1. 백엔드 API 서버 실행

#### 터미널 1 (백엔드)

```bash
# 가상환경 활성화 (아직 안 했다면)
# Windows: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate

# API 서버 실행 (기본 포트: 5001)
python api_server.py
```

**예상 출력:**
```
[*] Initializing database...
[+] Database already initialized
[*] Starting API server...
 * Serving Flask app 'api_server'
 * Running on http://127.0.0.1:5001
```

### 2. 프론트엔드 개발 서버 실행

#### 터미널 2 (프론트엔드)

```bash
# web-ui 디렉토리 이동
cd web-ui

# 개발 서버 실행 (기본 포트: 3000)
npm run dev
```

**예상 출력:**
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Ready in 2.5s
```

### 3. 서버 접속 확인

웹 브라우저에서 다음 URL로 접속:

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:5001/api/projects

---

## 웹 UI 사용법

### 1. 첫 화면 - 프로젝트 생성

1. 브라우저에서 `http://localhost:3000` 접속
2. **"프로젝트 관리"** 탭 선택
3. **"새 프로젝트"** 버튼 클릭
4. 프로젝트 정보 입력:
   - **프로젝트 이름**: 예) `Test Project`
   - **설명**: 예) `테스트용 프로젝트`
5. **"생성"** 버튼 클릭

### 2. 스캔 설정

1. **"스캔"** 탭 선택
2. 프로젝트가 자동 선택되어 있는지 확인
3. **"스캔 설정"** 서브탭에서 설정:

#### 기본 설정
- **대상 URL**: 스캔할 웹사이트 URL
  - 예: `http://example.com`
  - 예: `http://localhost:5000`
- **JS 경로** (선택사항): JavaScript 파일 경로
  - 예: `/static/js, /assets`

#### 분석 타입
- **JS 분석만**: JavaScript 파일만 빠르게 분석
- **전체 스캔**: 웹사이트 크롤링 + 상세 분석 (권장)

#### 분석 모드 (전체 스캔 선택 시)
- **⚡ 정적 분석만**: 빠른 패턴 매칭
- **🤖 AI 분석만**: GPT-4o로 숨겨진 엔드포인트 추론
- **🚀 정적 + AI 분석**: 가장 정확 (권장)

#### 크롤링 설정 (전체 스캔 선택 시)
- **크롤링 깊이**: 1~5단계 선택
  - 1단계: 현재 페이지만
  - 2단계: 링크된 페이지 포함
  - 3단계 이상: 재귀 크롤링
- **최대 페이지 수**: 10~200 페이지
  - 권장: 50 페이지

#### 추가 옵션
- **🔍 디렉토리 브루트포싱**: 숨겨진 경로 탐색

### 3. 스캔 시작

1. 모든 설정 완료 후 **"스캔 시작"** 버튼 클릭
2. **"진행 상황"** 서브탭에서 실시간 모니터링:
   - 원형 진행률 표시
   - 현재 상태 메시지
   - 스캔 ID

### 4. 결과 확인

#### 대시보드 (스캔 완료 후)
1. **"대시보드"** 탭 선택
2. 통계 확인:
   - 총 엔드포인트 수
   - Shadow API 수
   - 취약점 통계 (심각도별)
   - HTTP 메서드 분포

#### 히스토리
1. **"히스토리"** 탭 선택
2. 스캔 기록 목록 확인
3. 특정 스캔 클릭하여 상세 결과 보기:
   - 발견된 엔드포인트 목록
   - 검색/필터/정렬 기능
   - AI 배지 (AI로만 발견된 엔드포인트)
   - HTTP 메서드, 상태코드
   - 취약점 정보

---

## CLI 사용법 (고급)

### 1. JavaScript 파일 분석

```bash
python main.py analyze /path/to/js/files --recursive
```

### 2. 전체 스캔

```bash
python main.py full-scan http://example.com \
  --ai \
  --bruteforce \
  --crawl-depth 3 \
  --max-pages 100 \
  --validate
```

#### 옵션 설명:
- `--ai`: AI 분석 활성화 (정적 + AI)
- `--static-only`: 정적 분석만
- `--ai-only`: AI 분석만
- `--bruteforce`: 디렉토리 브루트포싱
- `--wordlist /path/to/wordlist.txt`: 커스텀 워드리스트
- `--crawl-depth N`: 크롤링 깊이 (1~5)
- `--max-pages N`: 최대 크롤링 페이지 수
- `--validate`: HTTP 엔드포인트 검증
- `--output /path/to/output`: 출력 디렉토리

### 3. 프록시 모드

```bash
python main.py proxy --host 127.0.0.1 --port 8080
```

---

## 테스트 앱 실행 (연습용)

프로젝트에 포함된 테스트 Flask 앱으로 스캐너를 테스트할 수 있습니다.

### 1. 테스트 앱 실행

#### Windows
```bash
cd test-app
start-test-app.bat
```

#### Linux/macOS
```bash
cd test-app
./start-test-app.sh
```

또는 수동 실행:
```bash
cd test-app
python app_improved.py
```

### 2. 테스트 앱 접속

- URL: http://localhost:5000
- 다양한 엔드포인트와 취약점 포함

### 3. 테스트 앱으로 스캔

웹 UI에서:
- **대상 URL**: `http://localhost:5000`
- **전체 스캔** 선택
- **정적 + AI 분석** 선택
- **브루트포싱** 활성화
- 스캔 시작!

---

## 문제 해결

### 1. 포트 충돌

**증상:** `Address already in use` 오류

**해결방법:**

#### Windows
```powershell
# 포트 5001 사용 중인 프로세스 찾기
netstat -ano | findstr :5001

# PID로 프로세스 종료
taskkill /PID <PID> /F
```

#### Linux/macOS
```bash
# 포트 5001 사용 중인 프로세스 찾기
lsof -i :5001

# 프로세스 종료
kill -9 <PID>
```

또는 다른 포트 사용:
```bash
# 백엔드
python api_server.py --port 5002

# 프론트엔드 (.env.local 수정 필요)
PORT=3001 npm run dev
```

### 2. OpenAI API 키 오류

**증상:** `Authentication failed` 또는 AI 분석 실패

**해결방법:**
1. API 키 확인:
   ```bash
   # Windows
   echo $env:OPENAI_API_KEY
   
   # Linux/macOS
   echo $OPENAI_API_KEY
   ```

2. API 키 유효성 확인: https://platform.openai.com/api-keys

3. 환경변수 재설정 (위 [OpenAI API 키 설정](#3-openai-api-키-설정-ai-분석-사용-시) 참조)

### 3. Python 패키지 설치 오류

**증상:** `ModuleNotFoundError` 또는 패키지 충돌

**해결방법:**
```bash
# pip 업그레이드
pip install --upgrade pip

# 캐시 클리어 후 재설치
pip cache purge
pip install -r requirements.txt --no-cache-dir

# 특정 패키지 재설치
pip uninstall <package-name>
pip install <package-name>
```

### 4. Node.js 패키지 설치 오류

**증상:** `npm ERR!` 또는 빌드 실패

**해결방법:**
```bash
cd web-ui

# node_modules 삭제
rm -rf node_modules package-lock.json

# 재설치
npm install

# 또는 yarn 사용
yarn install
```

### 5. 데이터베이스 오류

**증상:** `Database not initialized` 또는 테이블 없음

**해결방법:**
```bash
# 데이터베이스 재초기화
python setup_db.py

# 데이터베이스 파일 삭제 후 재생성 (주의: 모든 데이터 손실)
rm -rf data/*.db
python setup_db.py
```

### 6. 크롤링 실패

**증상:** `Connection refused` 또는 타임아웃

**해결방법:**
1. 대상 URL 확인 (http:// 또는 https:// 포함)
2. 네트워크 연결 확인
3. 방화벽/프록시 설정 확인
4. 타임아웃 증가 (config.yaml):
   ```yaml
   crawler:
     timeout: 30  # 초
   ```

### 7. CORS 오류 (프론트엔드)

**증상:** `Access-Control-Allow-Origin` 오류

**해결방법:**
- 백엔드 재시작 (CORS는 자동 설정됨)
- 브라우저 캐시 클리어 (Ctrl+Shift+Delete)

### 8. 메모리 부족

**증상:** 스캔 중 프로세스 종료 또는 느려짐

**해결방법:**
- 크롤링 깊이 낮추기 (1~2단계)
- 최대 페이지 수 줄이기 (25~50)
- AI 분석 대신 정적 분석만 사용
- 브루트포싱 비활성화

---

## 고급 설정

### 커스텀 워드리스트

브루트포싱용 커스텀 워드리스트 생성:

```bash
# wordlists 디렉토리에 파일 생성
nano wordlists/my_custom_wordlist.txt
```

```
/admin
/api
/v1
/v2
/dashboard
/console
/debug
# ... 더 추가
```

사용:
```bash
python main.py full-scan http://example.com \
  --bruteforce \
  --wordlist wordlists/my_custom_wordlist.txt
```

### 프로덕션 배포

#### 백엔드 (Gunicorn)
```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

#### 프론트엔드 (프로덕션 빌드)
```bash
cd web-ui
npm run build
npm start
```

또는 Nginx/Apache로 서빙.

---

## 추가 리소스

- **프로젝트 문서**: `PROJECT_DOCUMENTATION.md`
- **정확도 분석**: `ACCURACY_ANALYSIS_v2.md`
- **README**: `README.md`
- **GitHub Issues**: https://github.com/lee191/API_Scanner/issues

---

## 라이선스

이 프로젝트의 라이선스는 `LICENSE` 파일을 참조하세요.

---

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**설치 및 실행에 문제가 있나요?**
- GitHub Issues에 문의하거나
- 프로젝트 유지관리자에게 연락하세요

**Happy Scanning! 🚀🔍**
