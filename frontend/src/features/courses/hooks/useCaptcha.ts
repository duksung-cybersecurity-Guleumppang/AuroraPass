/**
 * useCaptcha 커스텀 훅
 *
 * CAPTCHA 관련 상태와 로직을 관리합니다.
 * - CAPTCHA 모달 상태 관리
 * - CAPTCHA 입력 및 검증
 * - 빠른 클릭 감지
 */

import { useRef, useState } from 'react';
import { CaptchaModalState } from '../../../shared/types/courses';
import { CAPTCHA_MESSAGES } from '../../../shared/constants/captcha';
import { fetchAfterReady } from '../../../shared/utils/healthz';
import { submitCaptchaApi } from './useCoursesApi';

/**
 * useCaptcha 훅의 반환 타입
 */
export interface UseCaptchaReturn {
  // === CAPTCHA 상태 ===
  captchaModal: CaptchaModalState;
  captchaInput: string;
  captchaMsg: string;
  uiCaptchaRequired: boolean;
  clickTimesRef: React.MutableRefObject<number[]>;

  // === CAPTCHA 상태 업데이트 함수 ===
  setCaptchaInput: (value: string) => void;
  setCaptchaModal: (state: CaptchaModalState) => void;
  setUiCaptchaRequired: (required: boolean) => void;
  setCaptchaMsg: (msg: string) => void;

  // === CAPTCHA 관련 함수 ===
  openCaptchaIfNeeded: (data: any) => boolean;
  submitCaptcha: (onSuccess: () => Promise<void>) => Promise<void>;
  refreshCaptcha: () => Promise<void>;
}

/**
 * useCaptcha 커스텀 훅
 *
 * CAPTCHA 인증 관련 모든 상태와 로직을 캡슐화합니다.
 *
 * @returns {UseCaptchaReturn} CAPTCHA 관련 상태와 함수들
 */
export function useCaptcha(): UseCaptchaReturn {
  // === CAPTCHA 상태 ===
  const [captchaModal, setCaptchaModal] = useState<CaptchaModalState>({ open: false });
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaMsg, setCaptchaMsg] = useState('');
  const [uiCaptchaRequired, setUiCaptchaRequired] = useState(false);

  // === 빠른 클릭 감지용 ref ===
  // 3초 내 5번 클릭 시 CAPTCHA 트리거 (ClickDetector 컴포넌트에서 사용)
  const clickTimesRef = useRef<number[]>([]);

  /**
   * 서버 응답에 따라 CAPTCHA 모달을 열어야 하는지 확인하는 함수
   *
   * Rate limiting에 걸렸거나 빠른 클릭이 감지되면 서버가 CAPTCHA를 요구합니다.
   * 이 함수는 서버 응답을 확인하여 CAPTCHA 모달을 표시합니다.
   *
   * @param {any} data - 서버 응답 데이터
   * @returns {boolean} CAPTCHA 모달이 열렸는지 여부 (true면 호출한 곳에서 처리 중단)
   */
  const openCaptchaIfNeeded = (data: any): boolean => {
    // 이미 UI에서 CAPTCHA가 필요한 상태인 경우
    if (uiCaptchaRequired) {
      // 모달이 닫혀있다면 다시 열기
      if (!captchaModal.open) {
        refreshCaptcha();
      }
      return true;
    }

    // 서버 응답에서 CAPTCHA 요구 여부 확인 (snake_case, camelCase 둘 다 지원)
    const requireCaptcha = data?.requireCaptcha ?? data?.require_captcha;
    if (requireCaptcha) {
      // CAPTCHA 데이터 추출
      const cap = data?.captcha || {};

      // CAPTCHA 모달 열기
      setCaptchaModal({
        open: true,
        captchaId: cap.captchaId || cap.captcha_id,
        audioPath: cap.audioPath || cap.audio_path
      });

      // UI 상태를 CAPTCHA 필요로 설정
      setUiCaptchaRequired(true);
      return true;
    }

    // CAPTCHA가 필요하지 않은 경우
    return false;
  };

  /**
   * CAPTCHA 인증을 제출하는 함수
   *
   * Rate limiting에 걸렸을 때 사용자가 CAPTCHA 모달에서 답을 입력하고 제출하면 호출됩니다.
   *
   * @param {Function} onSuccess - CAPTCHA 인증 성공 시 실행할 콜백 함수
   */
  const submitCaptcha = async (onSuccess: () => Promise<void>) => {
    // CAPTCHA ID가 없으면 종료
    if (!captchaModal.captchaId) return;

    // CAPTCHA 메시지 초기화
    setCaptchaMsg('');

    // API 호출
    const data = await submitCaptchaApi(captchaModal.captchaId, captchaInput);

    if (data?.success) {
      // CAPTCHA 인증 성공 처리

      // 1. CAPTCHA 모달 닫기
      setCaptchaModal({ open: false });
      setCaptchaInput('');
      setUiCaptchaRequired(false);
      clickTimesRef.current = [];

      // 2. 성공 콜백 실행 (부모 컴포넌트에서 정의한 로직)
      await onSuccess();
    } else {
      // CAPTCHA 인증 실패 처리
      setCaptchaMsg(data?.message || CAPTCHA_MESSAGES.VERIFICATION_FAILED);
    }
  };

  /**
   * 새로운 CAPTCHA를 생성하고 모달을 여는 함수
   *
   * CAPTCHA 모달에서 "새로고침" 버튼을 클릭하거나,
   * 빠른 클릭이 감지되었을 때 자동으로 호출됩니다.
   */
  const refreshCaptcha = async () => {
    // CAPTCHA 메시지 및 입력값 초기화
    setCaptchaMsg('');
    setCaptchaInput('');

    // 새로운 CAPTCHA 생성 API 호출
    const res = await fetchAfterReady('/api/captcha/generate');
    const data = await res.json();

    // CAPTCHA 모달 열기
    setCaptchaModal({
      open: true,
      captchaId: data?.captchaId,
      audioPath: data?.audioPath
    });
  };

  return {
    // 상태
    captchaModal,
    captchaInput,
    captchaMsg,
    uiCaptchaRequired,
    clickTimesRef,

    // 상태 업데이트 함수
    setCaptchaInput,
    setCaptchaModal,
    setUiCaptchaRequired,
    setCaptchaMsg,

    // CAPTCHA 관련 함수
    openCaptchaIfNeeded,
    submitCaptcha,
    refreshCaptcha
  };
}
