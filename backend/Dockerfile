# Python 3.9 이미지를 기반으로 합니다.
FROM python:3.9-slim

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# requirements.txt를 복사하고 의존성을 설치합니다.
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 소스 코드를 복사합니다.
COPY backend/ /app/

# 8000번 포트를 외부에 노출합니다.
EXPOSE 8000

# 애플리케이션을 실행합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]