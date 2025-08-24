# Aurora Pass 운영 가이드

## 📊 데이터베이스 구성

### PostgreSQL (관계형 데이터)
- **테이블 6개**: users, courses, carts, cart_items, enrollments, **captcha_files**
- **용도**: 사용자 정보, 강의 데이터, 장바구니, 수강신청 내역, CAPTCHA 오디오 파일

#### 테이블 상세
```sql
-- 사용자
users: id(UUID), username, email, password_hash, created_at

-- 강의
courses: id(string), title, capacity, enrolled_count, updated_at

-- 장바구니
carts: id(UUID), user_id(FK), created_at
cart_items: cart_id(FK), course_id(FK), added_at

-- 수강신청
enrollments: user_id(FK), course_id(FK), status, created_at

-- CAPTCHA 오디오 파일 (NEW!)
captcha_files: id, filename, answer, audio_data(bytea), content_type, created_at
```

### Redis (캐시/임시 데이터)
- **키 패턴**:
  - `captcha:{uuid}`: CAPTCHA 정답 (TTL 5분)
  - `rl:{user_id}`: 속도제한 카운터 (TTL 3초)
  - `unlock:{user_id}`: CAPTCHA 통과 임시 토큰 (TTL 30초)

## 🚀 로컬 실행 방법

### 권장 방법 (DB 포함)
```bash
# 개발용 전체 스택
docker compose -f docker-compose.dev.yml up -d --build

# 접속 주소
# - 프론트엔드: http://localhost:3000
# - 백엔드 API: http://localhost:8000
# - API 문서: http://localhost:8000/docs
# - 헬스체크: http://localhost:8000/readyz
```

### 레거시 방법 (DB 없음, 비권장)
```bash
# 기존 파일 시스템 기반
docker compose up -d --build
```

## 🔧 DB 상태 확인 방법

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

# CAPTCHA 파일
docker exec aurora_postgres psql -U appuser -d aurora -c "
SELECT id, filename, answer, length(audio_data) as file_size 
FROM captcha_files;
"
```

### Redis 조회
```bash
# 키 목록
docker exec aurora_redis redis-cli --scan

# 키 정보
docker exec aurora_redis redis-cli INFO keyspace

# 특정 키 조회 (예시)
docker exec aurora_redis redis-cli GET "captcha:some-uuid"
```

## 📂 Docker Compose 파일 정리

### 현재 상황
- `docker-compose.yml`: **구형 버전** (DB 없음, 파일 시스템 기반)
- `docker-compose.dev.yml`: **신형 버전** (PostgreSQL + Redis + 개발 편의 기능)
- `docker-compose.prod.yml`: **운영 스켈레톤** (하드닝, 리소스 제한)

### 권장 정리 방안

#### 옵션 1: 기존 파일 교체 (권장)
```bash
# 기존 파일 백업
mv docker-compose.yml docker-compose.legacy.yml

# 개발용을 기본으로 변경
cp docker-compose.dev.yml docker-compose.yml

# 결과: docker compose up 으로 바로 DB 포함 실행
```

#### 옵션 2: 명시적 분리 유지
```bash
# 개발: docker compose -f docker-compose.dev.yml up
# 운영: docker compose -f docker-compose.prod.yml up
# 레거시: docker compose -f docker-compose.legacy.yml up
```

## 🎯 테스트 시나리오

### API 테스트
```bash
# 1. 헬스체크
curl http://localhost:8000/readyz

# 2. 강의 목록
curl http://localhost:8000/api/courses

# 3. CAPTCHA 생성 (DB 기반)
curl http://localhost:8000/api/captcha/generate

# 4. 오디오 파일 다운로드
curl http://localhost:8000/api/captcha/audio/sample1 --output test.wav

# 5. 장바구니 추가
curl -X POST http://localhost:8000/api/cart \
  -H "Content-Type: application/json" \
  -d '{"courseId": "CS101"}'

# 6. 수강신청
curl -X POST http://localhost:8000/api/enroll
```

## 📈 성능/확장 고려사항

### 현재 제한사항
- **단일 컨테이너**: 백엔드 스케일링 제한
- **로컬 볼륨**: 데이터 지속성 (운영시 외부 스토리지 필요)
- **고정 사용자**: UUID 하드코딩 (실제 인증 필요)

### 향후 개선 방향
1. **로드 밸런싱**: 백엔드 다중 인스턴스
2. **DB 클러스터링**: PostgreSQL 읽기 복제본
3. **CDN**: 정적 파일 (오디오) 캐싱
4. **모니터링**: Prometheus + Grafana 메트릭
5. **로그 집계**: ELK 스택 또는 Loki

## 🔒 보안 체크리스트

### 개발 환경
- ✅ 컨테이너 네트워크 격리
- ✅ 환경변수 분리 (.env)
- ✅ Redis/DB 인증
- ⚠️ HTTPS 미적용 (로컬)

### 운영 환경 (향후)
- 🔲 TLS/SSL 인증서
- 🔲 시크릿 관리 (AWS Secrets Manager)
- 🔲 WAF (Web Application Firewall)
- 🔲 VPC 네트워크 분리
- 🔲 IAM 역할 기반 접근 제어
