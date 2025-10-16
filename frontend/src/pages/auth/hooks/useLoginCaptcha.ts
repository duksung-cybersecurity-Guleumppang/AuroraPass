/**
 * useLoginCaptcha 커스텀 훅
 *
 * 로그인 페이지의 CAPTCHA 관련 상태와 로직을 관리합니다.
 * - CAPTCHA 생성 및 새로고침
 * - CAPTCHA 검증
 * - 검증 상태 관리
 */

import { useEffect, useState } from 'react';
import { Captcha } from '../../../shared/types/login';
import { fetchAfterReady } from '../../../shared/utils/healthz';

/**
 * useLoginCaptcha 훅의 반환 타입
 */
export interface UseLoginCaptchaReturn {
  // === CAPTCHA 상태 ===
  captcha: Captcha | null;
  captchaInput: string;
  captchaMsg: string;
  captchaVerified: boolean;

  // === CAPTCHA 상태 업데이트 함수 ===
  setCaptchaInput: (value: string) => void;

  // === CAPTCHA 관련 함수 ===
  fetchCaptcha: () => Promise<void>;
  verifyCaptcha: () => Promise<void>;
}

/**
 * useLoginCaptcha 커스텀 훅
 *
 * 로그인 페이지의 CAPTCHA 인증 관련 모든 상태와 로직을 캡슐화합니다.
 * 컴포넌트 마운트 시 자동으로 CAPTCHA를 생성합니다.
 *
 * @returns {UseLoginCaptchaReturn} CAPTCHA 관련 상태와 함수들
 */
export function useLoginCaptcha(): UseLoginCaptchaReturn {
  // === CAPTCHA 상태 ===
  const [captcha, setCaptcha] = useState<Captcha | null>(null);
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaMsg, setCaptchaMsg] = useState('');
  const [captchaVerified, setCaptchaVerified] = useState(false);

  /**
   * 새로운 CAPTCHA를 서버에서 가져오는 함수
   *
   * 동작 순서:
   * 1. CAPTCHA 관련 상태 초기화
   * 2. GET /api/captcha/generate API 호출
   * 3. 새로운 CAPTCHA 데이터 저장
   */
  const fetchCaptcha = async () => {
    setCaptchaMsg('');
    setCaptchaVerified(false);
    setCaptchaInput('');

    try {
      const res = await fetchAfterReady('/api/captcha/generate');
      const data = await res.json();
      setCaptcha(data);
    } catch (error) {
      console.error('[useLoginCaptcha] CAPTCHA 생성 실패:', error);
      setCaptchaMsg('CAPTCHA 생성에 실패했습니다. 다시 시도해주세요.');
    }
  };

  /**
   * CAPTCHA 인증을 확인하는 함수
   *
   * 사용자가 입력한 CAPTCHA 답안을 서버에서 검증합니다.
   *
   * 동작 순서:
   * 1. 현재 CAPTCHA 존재 여부 확인
   * 2. POST /api/captcha/verify API 호출
   * 3. 검증 결과에 따라 상태 업데이트
   */
  const verifyCaptcha = async () => {
    if (!captcha) {
      setCaptchaMsg('CAPTCHA를 먼저 생성해주세요.');
      return;
    }

    if (!captchaInput.trim()) {
      setCaptchaMsg('CAPTCHA 답안을 입력해주세요.');
      return;
    }

    try {
      const res = await fetch('/api/captcha/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          captchaId: captcha.captchaId,
          userInput: captchaInput
        })
      });

      const data = await res.json();

      // 검증 결과 메시지 설정
      setCaptchaMsg(data.message || (data.success ? '인증 성공' : '인증 실패'));

      // 검증 성공 여부 저장
      setCaptchaVerified(!!data.success);
    } catch (error) {
      console.error('[useLoginCaptcha] CAPTCHA 검증 실패:', error);
      setCaptchaMsg('CAPTCHA 검증 중 오류가 발생했습니다.');
      setCaptchaVerified(false);
    }
  };

  /**
   * 컴포넌트 마운트 시 CAPTCHA 자동 생성
   */
  useEffect(() => {
    fetchCaptcha();
  }, []);

  return {
    // 상태
    captcha,
    captchaInput,
    captchaMsg,
    captchaVerified,

    // 상태 업데이트 함수
    setCaptchaInput,

    // CAPTCHA 관련 함수
    fetchCaptcha,
    verifyCaptcha
  };
}
