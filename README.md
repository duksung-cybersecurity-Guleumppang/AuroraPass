# 수강신청 시스템 프로젝트

캡차가 적용된 수강신청 시스템입니다. 백엔드는 FastAPI, 프론트엔드는 Vite + React + TypeScript(+Bun)로 구성되어 있으며 Docker Compose로 통합 실행합니다.

## 프로젝트 구조

- `backend/`: FastAPI 백엔드 (오디오 CAPTCHA/회원가입 구현)
- `frontend/`: Vite + React + TypeScript 프론트엔드 (로그인 UI, 오디오 CAPTCHA 연동)
- `docs/`: API 명세 문서
- `docker-compose.yml`: 백/프론트 컨테이너 정의

## 현재 구현 범위

- 백엔드 API
  - `GET /api/captcha/generate`: 오디오 CAPTCHA 발급 (오디오 경로/ID)
  - `POST /api/captcha/verify`: CAPTCHA 검증
  - `POST /api/users/register`: 회원가입(CAPTCHA 성공 필수, 인메모리 저장)
  - `POST /api/users/login`: 로그인(.env 또는 환경변수의 `LOGIN_USERNAME`/`LOGIN_PASSWORD`와 비교)
- 프론트엔드
  - 로그인 페이지 UI: 배경/로고, 아이디/비밀번호, 오디오 CAPTCHA(새로고침/검증), CAPTCHA 성공 시 로그인 버튼 활성화
  - 개발 서버 프록시: `/api`, `/static` → `backend:8000`

## 시작하기

### 요구사항

- Docker, Docker Compose

### 실행 방법

1) 컨테이너 빌드 및 기동
```bash
docker compose up --build -d
```

2) 접속 주소
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

3) 환경변수(선택)
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

## 개발 메모

- 프론트엔드 개발 서버는 Bun 기반(`oven/bun`)으로 동작합니다.
- 정적 오디오 파일은 백엔드에서 `/static/audio/*.wav` 경로로 서빙됩니다.
- 추후 구현 예정: 로그인/세션, 강의/장바구니/수강신청 API, 비정상 접근 탐지/재CAPTCHA, DB 영속화.

### CAPTCHA 정답 데이터
- 정답은 JSON 파일로 관리됩니다: `backend/static/audio/captcha_answers.json`
- 예시
```json
{
  "sample1.wav": "apple",
  "sample2.wav": "banana"
}
```

## API 명세 문서

- `docs/01_user_api.md`: 사용자 관련 API
- `docs/02_courses_api.md`: 강의 관련 API
- `docs/03_registration_api.md`: 수강신청 관련 API
- `docs/04_captcha_api.md`: CAPTCHA API 상세
