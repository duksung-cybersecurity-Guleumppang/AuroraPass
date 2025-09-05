/**
 * 캡차 모달 컴포넌트
 * 추가 인증이 필요할 때 캡차 인증을 위한 모달을 제공합니다.
 * 오디오 기반 캡차를 사용하여 사용자의 추가 인증을 요구합니다.
 */

import React from 'react';
import { CaptchaModalState } from '../../../shared/types/courses';
import styles from '../../../pages/courses/Courses.module.css';
import { CAPTCHA_MESSAGES } from '../../../shared/constants/captcha';

/**
 * CaptchaModal 컴포넌트의 props 인터페이스
 * @interface CaptchaModalProps
 * @property {CaptchaModalState} captchaModal - 캡차 모달의 상태 정보 (열림/닫힌 상태, 오디오 경로 등)
 * @property {string} captchaInput - 사용자가 입력한 캡차 답안
 * @property {string} captchaMsg - 캡차 관련 메시지 (성공, 오류 등)
 * @property {(value: string) => void} onInputChange - 캡차 입력값 변경 시 실행될 콜백 함수
 * @property {() => void} onSubmit - 캡차 답안 제출 시 실행될 콜백 함수
 * @property {() => void} onRefresh - 캡차 새로고침 시 실행될 콜백 함수
 * @property {() => void} onClose - 모달 닫기 시 실행될 콜백 함수
 */
interface CaptchaModalProps {
  captchaModal: CaptchaModalState;
  captchaInput: string;
  captchaMsg: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  onRefresh: () => void;
  onClose: () => void;
}

/**
 * CaptchaModal 컴포넌트 - 오디오 기반 캡차 인증 모달
 * @param {CaptchaModalProps} props - CaptchaModal 컴포넌트에 전달되는 props
 * @returns {JSX.Element | null} 캡차 모달 컴포넌트 또는 null (모달이 닫혀있는 경우)
 */
export default function CaptchaModal({
  captchaModal,
  captchaInput,
  captchaMsg,
  onInputChange,
  onSubmit,
  onRefresh,
  onClose
}: CaptchaModalProps) {
  // 모달이 열려있지 않으면 아무것도 렌더링하지 않음
  if (!captchaModal.open) return null;

  return (
    // 모달 오버레이 - 배경을 어둡게 처리하고 모달을 중앙에 위치
    <div className={styles.captchaModalOverlay}>
      <div className={styles.captchaModalContent}>
        {/* 모달 제목 */}
        <h3 className={styles.captchaModalTitle}>{CAPTCHA_MESSAGES.VERIFICATION_REQUIRED}</h3>
        
        {/* 캡차 설명 텍스트 */}
        <p className={styles.captchaModalDescription}>{CAPTCHA_MESSAGES.LISTEN_AND_ENTER}</p>
        
        {/* 오디오 캡차 컨테이너 */}
        <div className={styles.captchaAudioContainer}>
          <audio controls src={captchaModal.audioPath} className={styles.captchaAudio} />
        </div>
        
        {/* 캡차 입력 및 버튼 섹션 */}
        <div className={styles.captchaInputSection}>
          {/* 캡차 답안 입력 필드 */}
          <input
            value={captchaInput}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder="ENTER ANSWER"
            className={styles.captchaInput}
          />
          {/* 캡차 검증 버튼 */}
          <button onClick={onSubmit} className={styles.captchaSubmitButton}>VERIFY</button>
          {/* 캡차 새로고침 버튼 */}
          <button onClick={onRefresh} className={styles.captchaRefreshButton}>REFRESH</button>
        </div>
        
        {/* 캡차 관련 메시지 표시 (성공/오류 등) */}
        {captchaMsg && <p className={styles.captchaMessage}>{captchaMsg}</p>}
        
        {/* 모달 액션 버튼 */}
        <div className={styles.captchaModalActions}>
          {/* 모달 닫기 버튼 */}
          <button onClick={onClose} className={styles.captchaCloseButton}>CLOSE</button>
        </div>
      </div>
    </div>
  );
}