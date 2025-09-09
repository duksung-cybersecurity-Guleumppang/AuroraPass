/**
 * 캡차 관련 상수 정의
 * 클릭 감지 임계값과 시간 윈도우 등을 정의합니다.
 */

/**
 * 빠른 클릭 감지를 위한 상수들
 * @constant {object} CLICK_DETECTION
 * @property {number} WINDOW_MS - 클릭 감지 시간 윈도우 (밀리초)
 * @property {number} THRESHOLD - 캡차 트리거를 위한 클릭 횟수 임계값
 */
export const CLICK_DETECTION = {
  WINDOW_MS: 3000,  // 3초 윈도우
  THRESHOLD: 5,     // 5번 클릭
} as const;

/**
 * 캡차 관련 메시지
 * @constant {object} CAPTCHA_MESSAGES
 * @property {string} VERIFICATION_FAILED - 캡차 인증 실패 메시지
 * @property {string} VERIFICATION_REQUIRED - 추가 인증 요구 메시지
 * @property {string} LISTEN_AND_ENTER - 오디오 듣고 입력 안내 메시지
 */
export const CAPTCHA_MESSAGES = {
  VERIFICATION_FAILED: 'CAPTCHA 인증 실패',
  VERIFICATION_REQUIRED: 'Additional Verification Required',
  LISTEN_AND_ENTER: 'Please listen to the audio below and enter the word you hear.',
} as const;