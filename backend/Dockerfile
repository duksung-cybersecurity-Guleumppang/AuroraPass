# Python 3.9 이미지를 기반으로 합니다.
FROM python:3.9-slim

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# 전역 UTF-8 로케일/IO 인코딩 고정
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=UTF-8

# requirements.txt를 복사하고 의존성을 설치합니다.
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 소스 코드를 복사합니다.
COPY backend/ /app/

# 애플리케이션 포트를 환경변수 PORT로 노출합니다. 기본값은 런타임에서 결정됩니다.
ARG PORT
ENV PORT=${PORT}
EXPOSE ${PORT}

# 애플리케이션을 실행합니다.
CMD ["sh", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]