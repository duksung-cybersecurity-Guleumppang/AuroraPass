/**
 * useCart 커스텀 훅
 *
 * 장바구니 추가/제거 로직을 담당합니다.
 */

import { addToCartApi, removeFromCartApi } from './useCoursesApi';

/**
 * useCart 훅의 파라미터 타입
 */
export interface UseCartParams {
  /** CAPTCHA 확인 함수 */
  openCaptchaIfNeeded: (data: any) => boolean;
  /** 장바구니 새로고침 함수 */
  fetchCart: () => Promise<void>;
}

/**
 * useCart 훅의 반환 타입
 */
export interface UseCartReturn {
  /** 장바구니에 강의 추가 */
  addToCart: (courseId: string) => Promise<void>;
  /** 장바구니에서 강의 제거 */
  removeFromCart: (courseId: string) => Promise<void>;
}

/**
 * useCart 커스텀 훅
 *
 * 장바구니 관련 로직을 캡슐화합니다.
 * - 장바구니에 강의 추가
 * - 장바구니에서 강의 제거
 *
 * @param params - 훅 파라미터
 * @returns {UseCartReturn} 장바구니 관련 함수들
 */
export function useCart({ openCaptchaIfNeeded, fetchCart }: UseCartParams): UseCartReturn {
  /**
   * 강의를 장바구니에 추가하는 함수
   *
   * @param {string} courseId - 추가할 강의 ID
   */
  const addToCart = async (courseId: string) => {
    const data = await addToCartApi(courseId);
    if (openCaptchaIfNeeded(data)) return;
    await fetchCart();
  };

  /**
   * 장바구니에서 강의를 제거하는 함수
   *
   * @param {string} courseId - 제거할 강의 ID
   */
  const removeFromCart = async (courseId: string) => {
    const data = await removeFromCartApi(courseId);
    if (openCaptchaIfNeeded(data)) return;
    await fetchCart();
  };

  return {
    addToCart,
    removeFromCart
  };
}
