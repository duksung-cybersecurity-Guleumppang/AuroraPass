# Aurora Pass - 수강신청 시스템

캡차(오디오)와 비정상 접근 방지 로직이 적용된 수강신청 데모 서비스입니다. 백엔드는 FastAPI, 프론트엔드는 Vite + React + TypeScript(+Bun)로 구성되어 있으며 **PostgreSQL + Redis**를 활용한 완전한 DB 기반 아키텍처입니다.

## 데이터베이스 구성

### **PostgreSQL 15** (관계형 데이터)
- **8개 테이블**: users, courses, carts, cart_items, enrollments, **captcha_files**, **audio_sources**, **ko_source_answers**
- **현재 데이터**: 1명 사용자, 5개 강의, CAPTCHA 오디오 시스템(합성 지원), 1건 수강신청

| 테이블 | 용도 | 레코드 수 |
|---|---|---|
| `users` | 사용자 정보 (UUID, username, email, password_hash) | 1 |
| `courses` | 강의 정보 (id, title, capacity, enrolled_count) | 5 |
| `captcha_files` | **CAPTCHA 오디오 파일** (id, filename, answer, audio_data, 합성 메타데이터) | 가변 |
| `audio_sources` | **원본 오디오 소스** (한글/영어, bytea 저장) | 가변 |
| `ko_source_answers` | **한글 소스 정답 매핑** (파일명 → 질문/정답) | 가변 |
| `carts` | 사용자별 장바구니 | 1 |
| `cart_items` | 장바구니 아이템 | 0 |
| `enrollments` | 수강신청 내역 | 1 |

### 테이블별 역할 요약
* **captcha_files**: CAPTCHA 오디오와 정답 저장. 컬럼: id, filename, answer, audio_data(bytea), sample_rate, duration_ms, params(jsonb), pipeline_version, audio_hash, ko_source_id, en_source_id  
* **audio_sources**: 원본 오디오 파일 저장. 컬럼: id, language('ko'|'en'), original_filename, audio_data(bytea), sample_rate, duration_ms, audio_hash  
* **ko_source_answers**: 한글 소스 정답 매핑. 컬럼: ko_key(파일명), question, answer, ko_source_id  
* users: 사용자 계정. 컬럼: id(UUID), username, email, password_hash, created_at  
* courses: 강의 마스터. 컬럼: id, title, capacity, enrolled_count, updated_at  
* carts: 사용자별 장바구니 컨테이너. 컬럼: id(UUID), user_id(UUID), created_at  
* cart_items: 장바구니 항목. 복합 PK(cart_id, course_id), added_at  
* enrollments: 수강신청 결과. 복합 PK(user_id, course_id), status(ENROLLED 등), created_at  

### **Redis 7** (캐시/임시 데이터)
- **키 패턴**:
  - `captcha:{uuid}`: CAPTCHA 정답 (TTL 5분)
  - `rl:{user_id}`: 속도제한 카운터 (TTL 3초)  
  - `unlock:{user_id}`: CAPTCHA 통과 임시 토큰 (TTL 30초)

## 로컬 실행 방법

### 요구사항
- Docker Desktop (Docker, Docker Compose 포함)

### 실행 방법
```bash
# 1. 컨테이너 빌드 및 기동
docker compose up --build

# 2. 접속 주소
# - 프론트엔드: http://localhost:3000
# - 백엔드 API: http://localhost:8000
# - API 문서: http://localhost:8000/docs
# - 헬스체크: http://localhost:8000/readyz

# 3. 종료
docker compose down
```

## 단일 서버(EC2 등)에서 전체 스택 배포

아래 절차로 한 대 서버에 PostgreSQL/Redis/Backend/Frontend를 모두 Docker Compose로 기동할 수 있습니다.

1) 서버 준비
- Ubuntu 22.04 기준 Docker 설치 후 3000(프론트), 8000(백엔드) 포트를 보안그룹에서 허용합니다.

2) 환경 파일 생성(.env)
```bash
cp example.env .env
```
`.env`를 열어 값을 설정합니다.


3) 전체 스택 기동
```bash
docker compose up -d --build
docker compose ps
```

4) 확인
```bash
# 백엔드 상태
curl http://<SERVER_IP>:PORT/healthz

# 프론트 접속(브라우저)
http://<SERVER_IP>:PORT/
```

5) 운영 팁
- 코드 갱신: `git pull && docker compose up -d --build`
- 로그 확인: `docker compose logs backend -n 50` (frontend/postgres/redis 동일)
- 완전 정리(주의: 데이터 삭제): `docker compose down -v`


## AWS 설정 (도메인 연결 및 HTTPS 설정)

`https://rainbowwings.co.kr`처럼 포트 없이 접속하려면, EC2 보안그룹, DNS, Nginx 리버스 프록시, TLS 인증서 설정이 필요합니다. 아래 순서대로 진행하세요.

1) 보안그룹 열기(EC2)
- 인바운드 규칙에 80(HTTP), 443(HTTPS)을 추가합니다.
- 3000/8000 포트는 외부에 열지 않는 것을 권장합니다(내부용). 이미 열었다면 제거 또는 소스 제한을 고려하세요.

2) DNS 설정
- 도메인 관리 콘솔에서 A 레코드를 생성해 `도메인 → EC2 퍼블릭 IP`로 지정합니다.
- 예: `rainbowwings.co.kr → 11.22.33.44`

3) 애플리케이션 컨테이너 실행
- `.env`에서 포트를 설정하고 전체 스택을 기동합니다.
```bash
docker compose up -d --build
```
- 기본값 예시: `FRONT_PORT=3000`, `BACKEND_PORT=8000`

4) Nginx 설치(리버스 프록시)
```bash
sudo apt update -y && sudo apt install -y nginx
```

5) Nginx 서버 블록 생성
아래는 예시입니다.

```bash
sudo tee /etc/nginx/sites-available/rainbowwings.conf >/dev/null <<'NGINX'
server {
  listen 80;
  server_name rainbowwings.co.kr;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl;
  server_name rainbowwings.co.kr;

  # certbot 발급 후 아래 경로가 채워집니다
  ssl_certificate /etc/letsencrypt/live/rainbowwings.co.kr/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/rainbowwings.co.kr/privkey.pem;

  location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
  location /static/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
  }
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
  }
}
NGINX
sudo ln -s /etc/nginx/sites-available/rainbowwings.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

6) HTTPS 인증서 발급(무료, Certbot)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d rainbowwings.co.kr --email <your-email>@example.com --agree-tos --redirect
```
- 성공하면 Nginx 설정에 SSL 경로가 자동 반영되고, 80→443 리다이렉트가 켜집니다.

7) 확인
```bash
curl -I https://rainbowwings.co.kr/healthz     # 200 또는 301/302 후 200
open https://rainbowwings.co.kr                 # 브라우저 접속
```

문제 해결 팁
- DNS 전파(수분~최대 수십분) 대기 후 테스트하세요.
- Nginx 502/504: 컨테이너가 올라왔는지(`docker compose ps`)와 `.env`의 포트를 확인하세요.
- 인증서 오류: `certbot renew --dry-run`으로 갱신 테스트, 방화벽/보안그룹 80/443 열림 확인.


**한 줄 명령어로 PostgreSQL + Redis 포함 전체 스택 실행**

### 로그 확인 (문제 발생 시)
```bash
docker compose logs backend -n 50
docker compose logs frontend -n 50
```

## 데이터베이스 확인 방법

### PostgreSQL 조회
```bash
# 테이블 목록
docker exec aurora_postgres psql -U appuser -d aurora -c "\dt"

# 레코드 수 확인
docker exec aurora_postgres psql -U appuser -d aurora -c "
SELECT 'users' as table_name, count(*) FROM users UNION ALL
SELECT 'courses', count(*) FROM courses UNION ALL  
SELECT 'captcha_files', count(*) FROM captcha_files;
"

# 강의 목록
docker exec aurora_postgres psql -U appuser -d aurora -c "SELECT * FROM courses;"

# CAPTCHA 파일 (DB 저장)
docker exec aurora_postgres psql -U appuser -d aurora -c "
SELECT id, filename, answer, length(audio_data) as file_size_bytes 
FROM captcha_files;
"
```

### Redis 조회
```bash
# 키 목록  
docker exec aurora_redis redis-cli --scan

# 특정 키 조회
docker exec aurora_redis redis-cli GET "captcha:some-uuid"
```

### DB 버전/선택 확인
```bash
# 현재 실행 중 서비스(선택된 DB 종류 확인)
docker compose ps

# PostgreSQL 버전 확인
docker exec aurora_postgres psql -U appuser -d aurora -c "SELECT version();"

# Redis 버전 확인
docker exec aurora_redis redis-cli INFO server | grep redis_version
```

## 프로젝트 구조

```
AuroraPass/
├── docker-compose.yml          # 개발용 (PostgreSQL + Redis 포함)
├── backend/
│   ├── main.py                 # FastAPI 앱 + 헬스체크
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM 모델
│   │   ├── session.py          # DB 세션 팩토리
│   │   ├── redis_client.py     # Redis 클라이언트
│   │   └── init/               # DB 초기화 스크립트
│   ├── repositories/           # 리포지토리 패턴
│   ├── services/               # 비즈니스 로직
│   ├── api/                    # FastAPI 라우터
│   └── scripts/                # DB 유틸리티
├── frontend/                   # Vite + React + TypeScript
└── docs/                       # API 명세서
```

## API 테스트

```bash
# 헬스체크 (DB + Redis 상태)
curl http://localhost:8000/readyz

# 강의 목록
curl http://localhost:8000/api/courses

# CAPTCHA 생성 (DB 기반)
curl http://localhost:8000/api/captcha/generate

# 오디오 파일 다운로드 (DB에서 제공)
curl http://localhost:8000/api/captcha/audio/sample1 --output test.wav

# 장바구니 추가
curl -X POST http://localhost:8000/api/cart \
  -H "Content-Type: application/json" \
  -d '{"courseId": "CS101"}'

# 수강신청
curl -X POST http://localhost:8000/api/enroll
```

##  주요 기능

### 비정상 접근(CAPTCHA) 트리거
- **프론트엔드**: 페이지 어디서든 3초 내 5회 클릭 시 오디오 CAPTCHA 모달
- **백엔드**: 동일 사용자 3초 내 5회 이상 API 요청 시 CAPTCHA 요구
- **적용 경로**: `/api/courses`, `/api/cart`, `/api/enroll`, `/api/my-courses`

## CAPTCHA 오디오 합성 시스템

### 개요
DB에 저장된 한글/영어 오디오 소스를 합성하여 동적으로 CAPTCHA를 생성하는 자동화 시스템입니다.

### 주요 구성요소
- **원본 오디오 관리**: `audio_sources` 테이블에 한글/영어 WAV 파일을 bytea로 저장
- **정답 사전**: `ko_source_answers` 테이블에 파일명→정답 매핑 저장  
- **합성 엔진**: librosa 기반 오디오 처리 (피치변경, 믹싱, 게인조정)
- **원자적 소비**: `used` 플래그로 중복 사용 방지
- **자동 보충**: Top-up 스케줄러가 재고를 자동으로 유지

### 자동 합성 시스템
도커 시작 시 자동으로 다음이 실행됩니다:

1. **부팅 초기화** (`backend/scripts/bootstrap.py`)
   - DB 마이그레이션 전체 실행
   - 초기 CAPTCHA 시드 (static/audio 10개)
   - 정답 사전 UPSERT (static/real_answer.json)
   - 원본 오디오 UPSERT (tts_men_ko/, foreign_women_eng/)
   - 백그라운드 사전 합성 3개
   - Top-up 스케줄러 시작

2. **Top-up 스케줄러** (`backend/services/topup_scheduler.py`)
   - 60초 간격으로 재고 확인
   - 목표 재고(기본 1000개) 미달 시 자동 합성
   - 한글 오디오: 최근 30일 저사용 우선 + 랜덤
   - 영어 오디오: 무제한 랜덤 재사용

### 환경 변수 설정
`.env` 파일에 다음 변수들을 설정할 수 있습니다:

```bash
# CAPTCHA Top-up Scheduler Settings
INVENTORY_TARGET=1000        # 목표 재고 수량
TOP_UP_INTERVAL_SEC=60       # 점검 주기 (초)
MAX_PER_TICK=200            # 틱당 최대 합성 수량
BATCH_SIZE=50               # 배치 크기
```

### 수동 관리 명령어
```bash
# DB 상태 점검
docker exec aurorapass-backend-1 python scripts/inspect_db.py

# 수동 합성 (필요시)
docker exec aurorapass-backend-1 python scripts/synthesize_captcha.py --count 50

# 마이그레이션 수동 실행
docker exec aurorapass-backend-1 python scripts/bootstrap.py
```

### DB 디버깅/모니터링/SQL 실행
```bash
# 상세 디버깅 (전체)
docker exec aurorapass-backend-1 python scripts/debug_db.py

# 상세 디버깅 (섹션별)
docker exec aurorapass-backend-1 python scripts/debug_db.py schema
docker exec aurorapass-backend-1 python scripts/debug_db.py captcha
docker exec aurorapass-backend-1 python scripts/debug_db.py audio
docker exec aurorapass-backend-1 python scripts/debug_db.py answers
docker exec aurorapass-backend-1 python scripts/debug_db.py redis
docker exec aurorapass-backend-1 python scripts/debug_db.py activity
docker exec aurorapass-backend-1 python scripts/debug_db.py integrity

# 실시간 모니터링 (기본 10초 간격)
docker exec -it aurorapass-backend-1 python scripts/monitor_db.py
# 5초 간격
docker exec -it aurorapass-backend-1 python scripts/monitor_db.py 5

# SQL 실행기 (대화형)
docker exec -it aurorapass-backend-1 python scripts/sql_runner.py

# SQL 한 번에 실행
docker exec aurorapass-backend-1 python scripts/sql_runner.py "SELECT COUNT(*) FROM captcha_files"

# Redis 정답 키 확인
docker exec aurora_redis redis-cli --scan --pattern 'captcha:*'
docker exec aurora_redis redis-cli TTL captcha:<captchaId>
```

### 합성 규칙
- **파일명**: `ko_{koKey}__{enStem}_mix_{YYYYMMDD_HHMMSS}.wav`
- **중복 방지**: `audio_hash` 기반 ON CONFLICT DO NOTHING
- **원자적 소비**: FOR UPDATE SKIP LOCKED로 동시성 보장
- **만료 지원**: `expires_at` 컬럼으로 시한부 CAPTCHA 지원

## 로컬 개발 (옵션)

Docker 없이 각각 실행할 때:

```bash
# 백엔드 (FastAPI)
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드 (Vite + React + TypeScript)  
cd frontend
bun install
bun run dev -- --host --port 3000
```

## 구현 상세

### 로그인 플로우
1. 아이디/비밀번호 입력
2. 오디오 CAPTCHA 성공  
3. 로그인 API(`/api/users/login`) 성공 시 `/courses` 이동

### 수강신청 플로우  
1. 강의 목록 → 장바구니 담기/제거
2. 본 신청(`/api/enroll`) → 결과 메시지 표시
3. 정원/상태 갱신 (PostgreSQL 트랜잭션)

### CAPTCHA 시스템
- **생성**: DB에서 랜덤 선택 → Redis에 정답 저장 (TTL 5분)
- **제공**: `/api/captcha/audio/{id}`로 PostgreSQL에서 바이너리 스트리밍  
- **검증**: Redis 정답 확인 → 성공 시 30초간 임시 토큰 발급

---

**관련 문서**: `docs/` 폴더에서 상세 API 명세 확인