# 수강신청 시스템 프로젝트

이 프로젝트는 캡차가 적용된 수강신청 시스템입니다.

## 프로젝트 구조

- `backend/`: Python과 FastAPI를 사용한 백엔드 서버입니다.
- `frontend/`: React를 사용한 프론트엔드 애플리케이션입니다.
- `docs/`: API 명세 문서가 저장되어 있습니다.
- `docker-compose.yml`: Docker Compose를 사용하여 백엔드와 프론트엔드 서비스를 실행합니다.

## 시작하기

### 요구사항

- Docker
- Docker Compose

### 실행 방법

1.  프로젝트 루트 디렉터리에서 아래 명령어를 실행합니다.
    ```bash
    docker-compose up --build
    ```

2.  애플리케이션은 다음 주소에서 확인할 수 있습니다.
    -   **Frontend:** `http://localhost:3000`
    -   **Backend:** `http://localhost:8000`

## API 명세

자세한 API 명세는 `docs/` 폴더의 마크다운 파일들을 참고하세요.

- `docs/01_user_api.md`: 사용자 관련 API
- `docs/02_courses_api.md`: 강의 관련 API
- `docs/03_registration_api.md`: 수강신청 관련 API
