# Aurora Pass - 수강신청 시스템

캡차(오디오)와 비정상 접근 방지 로직이 적용된 수강신청 데모 서비스입니다. 백엔드는 FastAPI, 프론트엔드는 Vite + React + TypeScript(+Bun)로 구성되어 있으며 **PostgreSQL + Redis**를 활용한 완전한 DB 기반 아키텍처입니다.

## 데이터베이스 구성

### **PostgreSQL 15** (관계형 데이터)
- **6개 테이블**: users, courses, carts, cart_items, enrollments, **captcha_files**
- **현재 데이터**: 1명 사용자, 5개 강의, 3개 CAPTCHA 오디오 파일, 1건 수강신청

| 테이블 | 용도 | 레코드 수 |
|---|---|---|
| `users` | 사용자 정보 (UUID, username, email, password_hash) | 1 |
| `courses` | 강의 정보 (id, title, capacity, enrolled_count) | 5 |
| `captcha_files` | **CAPTCHA 오디오 파일** (id, filename, answer, audio_data) | 3 |
| `carts` | 사용자별 장바구니 | 1 |
| `cart_items` | 장바구니 아이템 | 0 |
| `enrollments` | 수강신청 내역 | 1 |

### 테이블별 역할 요약
* captcha_files: CAPTCHA 오디오와 정답 저장. 컬럼: id(파일 ID), filename, answer, audio_data(bytea), content_type, created_at  
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
├── docker-compose.prod.yml     # 운영용 스켈레톤 (외부 DB)
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

## AWS 배포 고려사항

### 개발용 vs 운영용 차이

| 구분 | 개발용 (docker-compose.yml) | 운영용 (docker-compose.prod.yml) |
|---|---|---|
| **DB 위치** | 컨테이너 내부 (postgres:15) | 외부 관리형 (RDS PostgreSQL) |
| **이미지 소스** | 로컬 빌드 (`build: .`) | ECR 레지스트리 (`image: <ECR>/app:tag`) |
| **코드 변경** | 볼륨 마운트로 즉시 반영 | 이미지 재배포 필요 |
| **보안** | 개발 편의성 우선 | 읽기전용, 리소스 제한 |
| **확장성** | 단일 컨테이너 | 로드밸런서 + 다중 인스턴스 |
| **비밀관리** | `.env` 파일 | AWS Secrets Manager |

### AWS 아키텍처
```
Internet → ALB → ECS Fargate Tasks → RDS PostgreSQL
                                   → ElastiCache Redis
```

### 배포 시 `docker-compose.prod.yml` 필요 이유
1. **외부 DB 연결**: RDS/ElastiCache 환경변수 사용
2. **보안 강화**: 읽기전용 파일시스템, 리소스 제한
3. **이미지 기반**: ECR 레지스트리에서 배포 이미지 pull
4. **ECS 태스크 정의**: Docker Compose를 ECS 태스크로 변환 시 참고

### AWS 배포 빠른 시작 (TL;DR)
```bash
# 0) 변수 채우기
cp deploy.env.example deploy.env
# deploy.env 열어 AWS_REGION, ACCOUNT_ID, IMAGE_TAG, DATABASE_URL, REDIS_URL 채우기

# 1) ECR 로그인 + 이미지 빌드/푸시 자동화
./scripts/deploy.sh

# 2) ECS(콘솔)에서 서비스의 태스크 정의 이미지 태그를 IMAGE_TAG로 갱신
#    → 백엔드/프론트엔드 모두 Force new deployment

# 3) ALB DNS로 접속해 확인
curl http://<alb-dns>/readyz   # 백엔드 상태
open http://<alb-dns>/         # 프론트엔드 화면
```

## AWS 배포 방법

AWS 콘솔/CLI를 이용해 ECS Fargate + ALB + RDS + ElastiCache로 배포하는 방법입니다.

### 0) 준비물
- AWS 계정, 권한(IAM AdministratorAccess 또는 동등 권한)
- 로컬: Docker, AWS CLI v2, Git, GitHub 계정(선택: CI/CD)
- 리전: ap-northeast-2(서울) 가정

### 1) ECR 리포지토리 생성
```bash
AWS_REGION=ap-northeast-2
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR=${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

aws ecr create-repository --repository-name aurora-backend --region $AWS_REGION || true
aws ecr create-repository --repository-name aurora-frontend --region $AWS_REGION || true

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
```

### 2) 이미지 빌드/푸시
```bash
TAG=$(git rev-parse --short HEAD || date +%s)

# Backend
docker buildx build \
  -t $ECR/aurora-backend:$TAG \
  -f backend/Dockerfile \
  --platform linux/amd64 \
  --push .

# Frontend
docker buildx build \
  -t $ECR/aurora-frontend:$TAG \
  -f frontend/Dockerfile \
  --platform linux/amd64 \
  --push frontend
```

### 3) RDS(PostgreSQL) / ElastiCache(Redis) 준비
- RDS 콘솔에서 PostgreSQL 인스턴스 생성 (예: db.t3.micro, 멀티AZ 비활성으로 시작)
- 보안 그룹에서 ECS 태스크 보안그룹에서 5432 접근 허용
- 엔드포인트, DB명/유저/비밀번호로 `DATABASE_URL` 구성:
```text
postgresql+psycopg2://<user>:<password>@<rds-endpoint>:5432/<dbname>
```
- ElastiCache Redis 클러스터 생성 (단일 샤드 시작)
- 보안 그룹에서 ECS 태스크 보안그룹에서 6379 접근 허용
- 엔드포인트로 `REDIS_URL` 구성:
```text
redis://<redis-endpoint>:6379/0
```

### 4) 시크릿 저장 (Secrets Manager 권장)
```bash
aws secretsmanager create-secret \
  --name AuroraPass/DATABASE_URL \
  --secret-string "postgresql+psycopg2://<user>:<password>@<rds-endpoint>:5432/<dbname>" \
  --region $AWS_REGION || true

aws secretsmanager create-secret \
  --name AuroraPass/REDIS_URL \
  --secret-string "redis://<redis-endpoint>:6379/0" \
  --region $AWS_REGION || true
```

### 5) ECS Fargate 클러스터/태스크/서비스 생성
1. ECS 콘솔에서 클러스터 생성(EC2가 아닌 Fargate)
2. 태스크 정의 생성(가족 이름: aurora-backend, aurora-frontend)
   - 런타임: Fargate, 네트워킹 모드: awsvpc, 플랫폼 1.4+
   - 컨테이너:
     - Backend: 이미지 `$ECR/aurora-backend:$TAG`, 포트 8000, 헬스체크 `GET /healthz`
       - 환경변수/시크릿: `DATABASE_URL`(Secrets Manager), `REDIS_URL`(Secrets Manager), `PORT=8000`
       - 로그: awslogs (그룹: /ecs/aurora-backend)
     - Frontend: 이미지 `$ECR/aurora-frontend:$TAG`, 포트 3000, 로그 awslogs
3. 서비스 생성(각 태스크 정의로 1개씩)
   - 서브넷: 프라이빗(태스크), 퍼블릭(ALB)
   - 보안 그룹: ALB ↔ ECS, ECS → RDS/Redis 허용
   - 오토스케일은 1개로 시작

### 5-1) docker-compose.prod.yml 변수 채우기 가이드
`docker-compose.prod.yml`은 운영 템플릿입니다. 실제 ECS에 직접 적용하지 않아도, "무엇을 채워야 하는지"를 보여주는 기준으로 사용합니다.

- `${ECR_REGISTRY}`: `<ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com`
- `${IMAGE_TAG}`: 배포할 이미지 태그(예: 커밋 해시 또는 날짜)
- `${AWS_REGION}`: 예) `ap-northeast-2`
- `${DATABASE_URL}`: RDS 연결 문자열
  - 예) `postgresql+psycopg2://<user>:<password>@<rds-endpoint>:5432/<dbname>`
- `${REDIS_URL}`: ElastiCache Redis 연결 문자열
  - 예) `redis://<redis-endpoint>:6379/0`

예시(치환 후 개념적으로 이런 값이 들어갑니다):
```yaml
services:
  backend:
    image: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/aurora-backend:20250101
    environment:
      - PORT=8000
      - DATABASE_URL=postgresql+psycopg2://appuser:apppass@aurora.xxxxxx.ap-northeast-2.rds.amazonaws.com:5432/aurora
      - REDIS_URL=redis://aurora-redis.xxxxxx.apn2.cache.amazonaws.com:6379/0
      - AWS_DEFAULT_REGION=ap-northeast-2
```

### 6) ALB 구성 (경로 기반 라우팅)
1. ALB 생성(퍼블릭 서브넷, 보안그룹 80/443 허용)
2. Target Group 2개:
   - tg-backend: HTTP:8000, 헬스체크 `/healthz`
   - tg-frontend: HTTP:3000, 헬스체크 `/`
3. 리스너 규칙(HTTP 80 → 이후 443 권장):
   - `/api/*`, `/static/*` → tg-backend
   - `/*` → tg-frontend
4. 각 ECS 서비스에 해당 Target Group 연결

### 7) 보안 그룹 요약
- ALB SG: Inbound 80/443 from 0.0.0.0/0 → Outbound to ECS SG
- ECS SG: Inbound from ALB SG(3000/8000) → Outbound to RDS/Redis SG(5432/6379)
- RDS SG: Inbound 5432 from ECS SG
- Redis SG: Inbound 6379 from ECS SG

### 8) 배포 확인
```bash
# ALB DNS 이름 확인 후 접속
curl http://<alb-dns>/readyz        # 백엔드 상태
curl http://<alb-dns>/              # 프론트엔드
```

### 9) 배포 확인 및 모니터링
- CloudWatch Logs에서 애플리케이션 로그 확인
- ECS 서비스 상태 및 태스크 모니터링  
- ALB Target Group 헬스체크 상태 점검

### 10) 리전 변경 팁
- `deploy.env`와 `docker-compose.prod.yml`에서 `${AWS_REGION}`만 변경하면 됩니다.
- ECR 레지스트리 도메인도 자동으로 리전에 맞게 바뀝니다: `<ACCOUNT_ID>.dkr.ecr.${AWS_REGION}.amazonaws.com`

### 11) IAM 권한(최소 필요 예시)
- ECR: `ecr:*`(push/pull), 최소한 `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:CompleteLayerUpload`, `ecr:InitiateLayerUpload`, `ecr:PutImage`, `ecr:UploadLayerPart`
- ECS: 서비스/태스크 정의 조회/배포(`ecs:*Describe*`, `ecs:UpdateService`, `iam:PassRole`)
- CloudWatch Logs: 로그 그룹 생성/쓰기
- Secrets Manager(선택): `secretsmanager:GetSecretValue`

### 12) 자주 겪는 오류와 해결법 (Troubleshooting)
- ALB 502/503: Target Group 헬스체크 실패 → 보안그룹/서브넷, 포트(8000/3000) 개방, 헬스엔드포인트(`/healthz`/`/`) 재확인
- 백엔드 기동 실패: `DATABASE_URL` 또는 `REDIS_URL` 오타/보안그룹 미설정 → 접속 문자열과 SG 규칙 점검
- 이미지 아키텍처 불일치: `--platform linux/amd64` 누락 → buildx 명령 재실행
- 로그가 안 보임: awslogs 설정과 권한 확인(로그 그룹 `/ecs/aurora-backend`, `/ecs/aurora-frontend`)
- RDS 연결 간헐 실패: 파라미터 그룹/서브넷 그룹, 멀티AZ 구성, 커넥션 수 제한 확인

### 13) 정리(Cleanup)
```bash
# 태그 이미지 삭제
aws ecr batch-delete-image \
  --repository-name aurora-backend \
  --image-ids imageTag=$TAG --region $AWS_REGION || true
aws ecr batch-delete-image \
  --repository-name aurora-frontend \
  --image-ids imageTag=$TAG --region $AWS_REGION || true

# (선택) 리포지토리 삭제
aws ecr delete-repository --repository-name aurora-backend --force --region $AWS_REGION || true
aws ecr delete-repository --repository-name aurora-frontend --force --region $AWS_REGION || true
```

### 배포 스크립트 사용(요약)
배포는 환경변수를 채우고 로컬 스크립트를 실행하면 ECR까지 자동으로 진행됩니다. ECS 서비스 업데이트는 마지막에 한 번 콘솔에서 수행합니다.

1) 환경변수 파일 생성/수정
```bash
cp deploy.env.example deploy.env
# deploy.env를 열어 아래 값을 채웁니다
# AWS_REGION, ACCOUNT_ID, IMAGE_TAG, DATABASE_URL, REDIS_URL 등
```

2) 스크립트 실행(이미지 빌드/푸시 자동)
```bash
./scripts/deploy.sh
```

3) ECS 서비스 업데이트(콘솔)
- 백엔드/프론트엔드 태스크 정의에서 컨테이너 이미지 경로를 다음으로 업데이트
  - Backend: ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/aurora-backend:${IMAGE_TAG}
  - Frontend: ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/aurora-frontend:${IMAGE_TAG}
- 해당 태스크 정의로 서비스를 배포(Force new deployment)
- ALB Target Group 헬스체크 및 CloudWatch Logs로 정상 동작 확인

참고: `scripts/deploy.sh`는 ECR 로그인/이미지 빌드 및 푸시까지 수행하며, ECS 서비스 업데이트는 안전을 위해 자동화하지 않았습니다.
변수 설명(예시):
```env
# deploy.env
AWS_REGION=ap-northeast-2
ACCOUNT_ID=123456789012
ECR_REGISTRY=${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
IMAGE_TAG=20250101
DATABASE_URL=postgresql+psycopg2://appuser:apppass@aurora.xxxxxx.ap-northeast-2.rds.amazonaws.com:5432/aurora
REDIS_URL=redis://aurora-redis.xxxxxx.apn2.cache.amazonaws.com:6379/0
```

##  주요 기능

### 비정상 접근(CAPTCHA) 트리거
- **프론트엔드**: 페이지 어디서든 3초 내 5회 클릭 시 오디오 CAPTCHA 모달
- **백엔드**: 동일 사용자 3초 내 5회 이상 API 요청 시 CAPTCHA 요구
- **적용 경로**: `/api/courses`, `/api/cart`, `/api/enroll`, `/api/my-courses`

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