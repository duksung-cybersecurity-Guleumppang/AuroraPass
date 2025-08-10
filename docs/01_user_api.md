# API 명세: 01. 사용자 가입

이 문서에서는 CAPTCHA 인증을 포함한 신규 사용자 가입 API를 설명합니다.

---

### 1. 사용자 가입 (회원가입)

사용자는 가입에 필요한 정보와 함께, 사전에 검증된 CAPTCHA 정보를 제출하여 회원가입을 요청합니다.

- **HTTP Method**: `POST`
- **Endpoint**: `/api/users/register`

#### 사전 조건

- 클라이언트는 사용자 가입 UI를 표시하기 전에 `GET /api/captcha/generate`를 호출하여 오디오 CAPTCHA를 사용자에게 제공해야 합니다. (상세 내용은 `04_captcha_api.md` 참조)
- 사용자는 오디오를 듣고 정답을 입력해야 합니다.

#### 요청 (Request)

- **Body**:

  ```json
  {
    "username": "newUser",
    "password": "password123!",
    "email": "newUser@example.com",
    "captchaId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "userInput": "사용자입력단어"
  }
  ```

  - `username` (string, required): 사용할 아이디
  - `password` (string, required): 사용할 비밀번호
  - `email` (string, required): 사용자 이메일
  - `captchaId` (string, required): `GET /api/captcha/generate`를 통해 발급받은 고유 식별자
  - `userInput` (string, required): 사용자가 CAPTCHA 오디오를 듣고 입력한 정답

#### 처리 절차

1.  서버는 요청을 받으면 `captchaId`와 `userInput`을 내부적으로 검증합니다.
2.  CAPTCHA 검증에 실패하면, 에러를 반환하고 사용자 등록 절차를 중단합니다.
3.  CAPTCHA 검증에 성공하면, `username`과 `email`이 기존에 사용 중인지 확인합니다.
4.  모든 검증을 통과하면, 새로운 사용자를 데이터베이스에 등록합니다.

#### 응답 (Response)

- **성공 (201 Created)**

  ```json
  {
    "userId": "12345",
    "username": "newUser",
    "message": "회원가입이 성공적으로 완료되었습니다."
  }
  ```

- **실패 (400 Bad Request)**

  - **CAPTCHA 인증 실패 시**:
    ```json
    {
      "error": "CAPTCHA 인증에 실패했습니다. 다시 시도해주세요."
    }
    ```
  - **사용자 이름 또는 이메일 중복 시**:
    ```json
    {
      "error": "이미 사용 중인 아이디 또는 이메일입니다."
    }
    ```
  - **요청 데이터 유효성 검사 실패 시**:
    ```json
    {
      "error": "입력값이 올바르지 않습니다. (예: 비밀번호 정책 위반)"
    }
    ```
