# API 명세: 04. CAPTCHA API

이 문서에서는 오디오 CAPTCHA 생성 및 검증을 위한 API를 상세히 설명합니다. 이 API는 사용자가 로봇이 아님을 증명해야 하는 모든 과정(예: 회원가입, 로그인)에서 사용됩니다.

---

### 1. 오디오 CAPTCHA 생성

새로운 오디오 CAPTCHA와 고유 키를 요청합니다.

- **HTTP Method**: `GET`
- **Endpoint**: `/api/captcha/generate`

#### 요청 (Request)

쿼리 파라미터나 요청 본문이 필요 없습니다.

#### 응답 (Response)

- **성공 (200 OK)**

  ```json
  {
    "captchaId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "audioPath": "/captcha-audio/sample1.wav"
  }
  ```

  - `captchaId` (string, UUID): 생성된 CAPTCHA의 고유 식별자입니다. 검증 단계에서 이 값을 사용해야 합니다.
  - `audioPath` (string): 재생할 오디오 파일의 경로입니다. 클라이언트는 이 경로를 사용하여 오디오를 재생해야 합니다.

- **실패 (500 Internal Server Error)**

  ```json
  {
    "error": "CAPTCHA 생성에 실패했습니다."
  }
  ```

---

### 2. CAPTCHA 검증

사용자가 입력한 단어가 오디오 CAPTCHA의 정답과 일치하는지 검증합니다.

- **HTTP Method**: `POST`
- **Endpoint**: `/api/captcha/verify`

#### 요청 (Request)

- **Body**:

  ```json
  {
    "captchaId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "userInput": "사용자입력단어"
  }
  ```

  - `captchaId` (string, required): `GET /api/captcha/generate`를 통해 발급받은 고유 식별자입니다.
  - `userInput` (string, required): 사용자가 오디오를 듣고 입력한 단어입니다.

#### 응답 (Response)

- **성공 (200 OK)**

  ```json
  {
    "success": true,
    "message": "CAPTCHA 인증에 성공했습니다."
  }
  ```

  - `success` (boolean): `true`는 인증 성공을 의미합니다. 이 경우, 회원가입 등 다음 단계를 진행할 수 있습니다.

- **실패 (400 Bad Request)**

  - **정답이 틀린 경우**:
    ```json
    {
      "success": false,
      "message": "입력한 내용이 올바르지 않습니다."
    }
    ```
  - **`captchaId`가 유효하지 않거나 만료된 경우**:
    ```json
    {
      "success": false,
      "message": "CAPTCHA 세션이 유효하지 않습니다. 다시 시도해주세요."
    }
    ```
