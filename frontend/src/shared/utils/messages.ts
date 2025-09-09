/**
 * 메시지 포맷팅 유틸리티 함수들
 * 동적 메시지 생성을 위한 헬퍼 함수들을 제공합니다.
 */

import { ENROLLMENT_MESSAGES } from '../constants/courses';

/**
 * 수강신청 결과 메시지를 포맷팅합니다.
 * @param {number} successCount - 성공한 수강신청 건수
 * @param {number} failCount - 실패한 수강신청 건수
 * @returns {string} 포맷팅된 결과 메시지
 */
export function formatEnrollmentResult(successCount: number, failCount: number): string {
  return `신청 완료: 성공 ${successCount}건, 실패 ${failCount}건`;
}

/**
 * 장바구니 개수 메시지를 포맷팅합니다.
 * @param {number} count - 장바구니에 담긴 과목 수
 * @returns {string} 포맷팅된 장바구니 메시지
 */
export function formatCartCount(count: number): string {
  return `장바구니 ${count}개`;
}

/**
 * 로딩 상태에 따른 버튼 텍스트를 반환합니다.
 * @param {boolean} isLoading - 로딩 상태
 * @param {string} defaultText - 기본 텍스트
 * @param {string} loadingText - 로딩 중 텍스트
 * @returns {string} 상태에 맞는 버튼 텍스트
 */
export function getButtonText(isLoading: boolean, defaultText: string, loadingText: string): string {
  return isLoading ? loadingText : defaultText;
}