/**
 * 수강신청 페이지 관련 타입 정의
 * 강의 정보와 캡차 모달 상태를 위한 타입들을 정의합니다.
 */

import React from 'react';

/**
 * 강의 정보 타입
 * @interface Course
 * @property {string} courseId - 강의 ID
 * @property {string} title - 강의명
 * @property {string} professor - 교수명
 * @property {string} schedule - 수업 시간표
 * @property {number} capacity - 정원
 * @property {number} enrolled - 현재 신청자 수
 */
export type Course = {
  courseId: string;
  title: string;
  professor: string;
  schedule: string;
  capacity: number;
  enrolled: number;
  department?: string;
  year?: number;
  semester?: number;
  level?: string;
  category?: string;
  theoryHours?: number;
  practiceHours?: number;
};

/**
 * 캡차 모달 상태 타입
 * @interface CaptchaModalState
 * @property {boolean} open - 모달 열림 상태
 * @property {string} [captchaId] - 캡차 ID (선택적)
 * @property {string} [audioPath] - 오디오 파일 경로 (선택적)
 */
export interface CaptchaModalState {
  open: boolean;
  captchaId?: string;
  audioPath?: string;
}

/**
 * 클릭 감지 컴포넌트의 props 타입
 * @interface ClickDetectorProps
 * @property {boolean} enabled - 클릭 감지 활성화 여부
 * @property {function} onTrigger - 임계값 도달 시 실행될 콜백 함수
 * @property {React.MutableRefObject<number[]>} clickTimesRef - 클릭 시간을 저장하는 ref
 */
export interface ClickDetectorProps {
  enabled: boolean;
  onTrigger: () => void | Promise<void>;
  clickTimesRef: React.MutableRefObject<number[]>;
}