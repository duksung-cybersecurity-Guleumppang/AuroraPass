/**
 * useCourses 커스텀 훅 (메인 훅)
 *
 * 여러 sub-hooks를 조합하여 수강신청 시스템의 모든 기능을 제공합니다.
 * - useCoursesData: 데이터 조회 및 상태 관리
 * - useCart: 장바구니 관리
 * - useEnrollment: 수강신청 관리
 * - useCaptcha: CAPTCHA 인증
 */

import { useMemo, useState } from 'react';
import { CaptchaModalState } from '../../../shared/types/courses';
import { useCaptcha } from './useCaptcha';
import { useCoursesData } from './useCoursesData';
import { useCart } from './useCart';
import { useEnrollment } from './useEnrollment';

/**
 * useCourses 훅의 반환 타입
 */
export interface UseCoursesReturn {
  // 강의 관련 상태
  courses: any[];
  cart: any[];
  enrolledCourses: any[];
  cartIdSet: Set<string>;

  // UI 상태
  loading: boolean;
  message: string;

  // CAPTCHA 관련 상태
  captchaModal: CaptchaModalState;
  captchaInput: string;
  captchaMsg: string;
  uiCaptchaRequired: boolean;
  clickTimesRef: React.MutableRefObject<number[]>;

  // 액션 함수들
  fetchCourses: (options?: { suppressCaptcha?: boolean }) => Promise<void>;
  searchCourses: (params?: {
    keyword?: string;
    year?: number;
    semester?: number;
    level?: string;
    category?: string;
    department?: string;
    page?: number;
    pageSize?: number;
    sort?: 'recent' | 'name' | 'code';
    order?: 'asc' | 'desc';
  }) => Promise<void>;
  fetchCart: (options?: { suppressCaptcha?: boolean }) => Promise<void>;
  addToCart: (courseId: string) => Promise<void>;
  removeFromCart: (courseId: string) => Promise<void>;
  enroll: () => Promise<void>;
  enrollSingle: (courseId: string) => Promise<void>;
  cancelEnrollment: (courseId: string) => Promise<void>;
  submitCaptcha: () => Promise<void>;
  refreshCaptcha: () => Promise<void>;
  setCaptchaInput: (value: string) => void;
  setCaptchaModal: (state: CaptchaModalState) => void;
  setUiCaptchaRequired: (required: boolean) => void;
}

/**
 * useCourses 메인 훅
 *
 * 여러 sub-hooks를 조합하여 수강신청 시스템의 모든 기능을 제공합니다.
 *
 * @returns {UseCoursesReturn} 수강신청 관련 상태와 함수들
 */
export function useCourses(): UseCoursesReturn {
  // UI 상태 관리
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // CAPTCHA 관련 상태 및 함수
  const {
    captchaModal,
    captchaInput,
    captchaMsg,
    uiCaptchaRequired,
    clickTimesRef,
    setCaptchaInput,
    setCaptchaModal,
    setUiCaptchaRequired,
    openCaptchaIfNeeded,
    submitCaptcha: submitCaptchaBase,
    refreshCaptcha
  } = useCaptcha();

  // 데이터 조회 및 상태 관리
  const {
    courses,
    cart,
    enrolledCourses,
    setCourses,
    setCart,
    setEnrolledCourses,
    fetchCourses: fetchCoursesData,
    searchCourses: searchCoursesData,
    fetchCart: fetchCartData,
    fetchMyCourses: fetchMyCoursesData
  } = useCoursesData();

  // CAPTCHA 체크를 포함한 래퍼 함수들
  const fetchCourses = async (options?: { suppressCaptcha?: boolean }) => {
    const data = await fetchCoursesData(options);
    if (!options?.suppressCaptcha) {
      openCaptchaIfNeeded(data);
    }
  };

  const searchCourses = async (params?: any) => {
    const data = await searchCoursesData(params);
    openCaptchaIfNeeded(data);
  };

  const fetchCart = async (options?: { suppressCaptcha?: boolean }) => {
    const data = await fetchCartData(options);
    if (!options?.suppressCaptcha) {
      openCaptchaIfNeeded(data);
    }
  };

  const fetchMyCourses = async (options?: { suppressCaptcha?: boolean }) => {
    const data = await fetchMyCoursesData(options);
    if (!options?.suppressCaptcha) {
      openCaptchaIfNeeded(data);
    }
  };

  // 장바구니 관리
  const { addToCart, removeFromCart } = useCart({
    openCaptchaIfNeeded,
    fetchCart
  });

  // 수강신청 관리
  const { enroll, enrollSingle, cancelEnrollment } = useEnrollment({
    courses,
    cart,
    setCourses,
    setEnrolledCourses,
    setLoading,
    setMessage,
    openCaptchaIfNeeded,
    fetchCourses,
    fetchCart,
    fetchMyCourses
  });

  // CAPTCHA 인증 제출
  const submitCaptcha = async () => {
    await submitCaptchaBase(async () => {
      // CAPTCHA 인증 성공 시 실행할 로직
      setEnrolledCourses(prev => {
        const newCourses = cart
          .filter(course => !prev.some(enrolled => enrolled.courseId === course.courseId))
          .map(course => ({ ...course, enrolled: (course.enrolled ?? 0) + 1 }));
        return [...prev, ...newCourses];
      });

      setMessage(`수강신청 완료: ${cart.length}개 과목`);
      await fetchCourses();
      await fetchCart();
      await fetchMyCourses();
    });
  };

  // 장바구니 ID Set (성능 최적화)
  const cartIdSet = useMemo(() => new Set(cart.map((c) => c.courseId)), [cart]);

  return {
    // 상태
    courses,
    cart,
    enrolledCourses,
    cartIdSet,
    loading,
    message,
    captchaModal,
    captchaInput,
    captchaMsg,
    uiCaptchaRequired,
    clickTimesRef,

    // 함수들
    fetchCourses,
    searchCourses,
    fetchCart,
    addToCart,
    removeFromCart,
    enroll,
    enrollSingle,
    cancelEnrollment,
    submitCaptcha,
    refreshCaptcha,
    setCaptchaInput,
    setCaptchaModal,
    setUiCaptchaRequired
  };
}