/**
 * 로그인 페이지 관련 타입 정의
 * 캡차 정보를 위한 타입을 정의합니다.
 */

/**
 * 캡차 정보 타입
 * @interface Captcha
 * @property {string} captchaId - 캡차 고유 식별자
 * @property {string} audioPath - 캡차 오디오 파일 경로
 */
export type Captcha = { 
    captchaId: string; 
    audioPath: string; 
};