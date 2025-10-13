# 취약한 테스트 애플리케이션용 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 5000

# 환경변수
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# uploads 디렉토리 생성
RUN mkdir -p uploads

# 애플리케이션 실행 (개선된 버전 사용)
CMD ["python", "app_improved.py"]
