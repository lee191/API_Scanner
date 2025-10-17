# 🚀 API Scanner - 빠른 시작 가이드

## 5분 안에 시작하기

### 1️⃣ 프로젝트 다운로드
```bash
git clone https://github.com/lee191/API_Scanner.git
cd API_Scanner
```

### 2️⃣ 백엔드 설정
```bash
# Python 가상환경 생성
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python setup_db.py
```

### 3️⃣ 프론트엔드 설정
```bash
cd web-ui
npm install
cd ..
```

### 4️⃣ OpenAI API 키 설정 (AI 분석 사용 시)
```bash
# Windows
$env:OPENAI_API_KEY = "sk-your-api-key-here"

# Linux/macOS
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 5️⃣ 서버 실행

**터미널 1 (백엔드):**
```bash
python api_server.py
```

**터미널 2 (프론트엔드):**
```bash
cd web-ui
npm run dev
```

### 6️⃣ 웹 브라우저 접속
```
http://localhost:3000
```

---

## 첫 스캔 실행하기

### 웹 UI 사용:
1. **프로젝트 관리** → **새 프로젝트** 생성
2. **스캔** 탭 선택
3. **대상 URL** 입력 (예: `http://example.com`)
4. **전체 스캔** 선택
5. **정적 + AI 분석** 선택 (권장)
6. **스캔 시작** 버튼 클릭!

### CLI 사용:
```bash
python main.py full-scan http://example.com --ai --validate
```

---

## 테스트 앱으로 연습하기

### 1. 테스트 앱 실행
```bash
cd test-app
python app_improved.py
```

### 2. 웹 UI에서 스캔
- **대상 URL**: `http://localhost:5000`
- **전체 스캔** + **AI 분석** 활성화
- **브루트포싱** 활성화
- 스캔 시작!

---

## 주요 기능

### 📊 분석 타입
- **JS 분석만**: 빠른 분석 (수초)
- **전체 스캔**: 완전한 분석 (수분)

### 🤖 분석 모드
- **정적 분석**: 패턴 매칭 (빠름)
- **AI 분석**: GPT-4o 기반 (정확)
- **정적 + AI**: 최고 정확도 (권장)

### 🕸️ 크롤링 깊이
- **1단계**: 현재 페이지만
- **2~3단계**: 링크된 페이지 포함
- **4~5단계**: 깊은 크롤링

### 🔍 추가 기능
- **브루트포싱**: 숨겨진 경로 탐색
- **취약점 스캔**: 보안 취약점 탐지
- **HTTP 검증**: 엔드포인트 유효성 확인

---

## 문제 해결

### 포트 충돌
```bash
# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :5001
kill -9 <PID>
```

### 패키지 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 데이터베이스 오류
```bash
python setup_db.py
```

---

## 더 자세한 가이드

전체 설치 가이드는 `INSTALLATION_GUIDE.md`를 참조하세요.

**Happy Scanning! 🎉**
