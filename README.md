# Aurora Pass - 수강신청 시스템

캡차(오디오)와 비정상 접근 방지 로직이 적용된 수강신청 데모 서비스입니다. 백엔드는 FastAPI, 프론트엔드는 Vite + React + TypeScript(+Bun)로 구성되어 있으며 Docker Compose로 통합 실행합니다.

## 프로젝트 구조

- `backend/`: FastAPI 백엔드 (오디오 CAPTCHA/회원가입 구현)
- `frontend/`: Vite + React + TypeScript 프론트엔드 (로그인 UI, 오디오 CAPTCHA 연동)
- `docs/`: API 명세 문서
- `docker-compose.yml`: 백/프론트 컨테이너 정의

## 현재 구현 범위(요약)

- 백엔드 API
  - `GET /api/captcha/generate`: 오디오 CAPTCHA 발급 (오디오 경로/ID)
  - `POST /api/captcha/verify`: CAPTCHA 검증
  - `POST /api/users/register`: 회원가입(CAPTCHA 성공 필수, 인메모리 저장)
  - `POST /api/users/login`: 로그인(.env 또는 환경변수의 `LOGIN_USERNAME`/`LOGIN_PASSWORD`와 비교)
  - `GET /api/courses`: 강의 목록 조회
  - `GET /api/cart`: 장바구니 조회
  - `POST /api/cart`: 장바구니 추가
  - `DELETE /api/cart/{courseId}`: 장바구니 제거
  - `POST /api/enroll`: 본 신청(정원/중복 간단 처리)
  - `GET /api/my-courses`: 신청 결과 조회
- 프론트엔드
  - 로그인 페이지 UI: 배경/로고, 아이디/비밀번호(초기 빈칸), 오디오 CAPTCHA(새로고침/검증), CAPTCHA 성공 시 로그인 버튼 활성화 → 성공 시 `/courses` 이동
  - 수강신청 페이지 UI(`/courses`): 카드형 강의 목록, 장바구니 패널, 본 신청 버튼(데모 API 연동), 담긴 과목은 버튼이 '담김'으로 비활성화 표시
  - 전역 빠른 클릭 감지: 페이지 어디서든 3초 내 5회 클릭 시 오디오 CAPTCHA 모달 표시(5.png 흐름)
  - 개발 서버 프록시: `/api`, `/static` → `backend:8000`

## 시작하기

### 요구사항

- Docker Desktop (Docker, Docker Compose 포함)

### 실행 방법 (Docker Compose 권장)

1) 컨테이너 빌드 및 기동
```bash
docker compose up --build -d
```

2) 접속 주소
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

3) 종료
```bash
docker compose down
```

4) 로그 확인(문제 발생 시)
```bash
docker compose logs backend -n 200 | cat
docker compose logs frontend -n 200 | cat
```

5) 환경변수(선택)
- 프론트 로그인 폼 기본값을 지정하려면 `frontend/.env` 파일을 생성하세요.
```bash
VITE_LOGIN_USERNAME=demo_user
VITE_LOGIN_PASSWORD=demo_password
```

- 백엔드 로그인 비교용 환경변수는 `LOGIN_USERNAME`, `LOGIN_PASSWORD` 입니다.
  - 기본값은 `docker-compose.yml`의 `backend.environment`에서 주입됩니다.
  - 필요 시 루트 `.env` 또는 `backend/.env`에 동일 키를 설정하면 `python-dotenv`가 로드합니다.

```bash
LOGIN_USERNAME=demo_user
LOGIN_PASSWORD=demo_password
```

### 로컬 개발 실행 (옵션)

도커 없이 각각 실행해 개발할 때 사용합니다.

- 백엔드(FastAPI)
```bash
# uv 사용 권장 (미설치 시 https://docs.astral.sh/uv/ 참고)
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- 프론트엔드(Vite + React + TypeScript)
```bash
cd frontend
bun install
bun run dev -- --host --port 3000
```

프론트 개발 서버는 프록시로 `/api`, `/static`을 `http://localhost:8000`으로 전달합니다.

## 개발 메모

- 프론트엔드 개발 서버는 Bun 기반(`oven/bun`)으로 동작합니다.
- 정적 오디오 파일은 백엔드에서 `/static/audio/*.wav` 경로로 서빙됩니다.
- 추후 구현 예정: 로그인/세션, 강의/장바구니/수강신청 API, 비정상 접근 탐지/재CAPTCHA, DB 영속화.

### 비정상 접근(CAPTCHA) 트리거
- 프론트(UI): 페이지 어디서든 3초 내 5회 클릭 시 오디오 CAPTCHA 모달을 표시합니다.
- 백엔드(API): 동일 사용자 기준 3초 내 5회 이상 요청 시 서버가 CAPTCHA를 요구합니다.
- 적용 경로: `/api/courses`, `/api/cart`(GET/POST/DELETE), `/api/enroll`, `/api/my-courses`
- 응답 예(요구 시):
```json
{
  "requireCaptcha": true,
  "captcha": { "captchaId": "...", "audioPath": "/static/audio/sample1.wav" }
}
```
프론트에서 모달로 오디오 재생/정답 제출 후 `/api/enroll/unlock`을 통해 1회 신청이 허용됩니다.

## 구현 상세(확인용 체크리스트)
- 로그인 플로우: 아이디/비밀번호 입력 → 오디오 CAPTCHA 성공 → 로그인 API(`/api/users/login`) 성공 시 `/courses` 이동
- 수강신청 플로우: 강의 목록 → 장바구니 담기/제거 → 본 신청(`/api/enroll`) → 결과 메시지 표시 및 정원/상태 갱신
- 장바구니 버튼 상태: 이미 담긴 과목 또는 정원 초과 과목은 비활성화
- 데모 데이터/정답 파일: 변경 즉시 반영, 백엔드 재시작으로 인메모리 상태 초기화

### CAPTCHA 정답 데이터
- 정답은 JSON 파일로 관리됩니다: `backend/static/audio/captcha_answers.json`
- 예시
```json
{
  "sample1.wav": "apple",
  "sample2.wav": "banana"
}
```

### 강의 데모 데이터
- 강의 목록 데모 데이터는 JSON 파일로 관리됩니다: `backend/static/demo/courses.json`
- 값을 수정하면 API와 UI에 반영됩니다.

## API 명세 문서

- `docs/01_user_api.md`: 사용자 관련 API
- `docs/02_courses_api.md`: 강의 관련 API
- `docs/03_registration_api.md`: 수강신청 관련 API
- `docs/04_captcha_api.md`: CAPTCHA API 상세
