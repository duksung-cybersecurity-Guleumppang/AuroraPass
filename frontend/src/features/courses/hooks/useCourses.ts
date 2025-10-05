/**
 * 수강신청 관련 상태와 로직을 관리하는 커스텀 훅
 * 강의 목록, 장바구니, 수강신청 등의 비즈니스 로직을 포함합니다.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { Course, CaptchaModalState } from '../../../shared/types/courses';
import { formatEnrollmentResult } from '../../../shared/utils/messages';
import { CAPTCHA_MESSAGES } from '../../../shared/constants/captcha';
import { fetchAfterReady } from '../../../shared/utils/healthz';

/**
 * useCourses 훅의 반환 타입
 */
export interface UseCoursesReturn {
  // 강의 관련 상태
  courses: Course[];
  cart: Course[];
  enrolledCourses: Course[];
  cartIdSet: Set<string>;

  // UI 상태
  loading: boolean;
  message: string;

  // 캡차 관련 상태
  captchaModal: CaptchaModalState;
  captchaInput: string;
  captchaMsg: string;
  uiCaptchaRequired: boolean;
  clickTimesRef: React.MutableRefObject<number[]>;

  // 액션 함수들
  fetchCourses: () => Promise<void>;
  fetchCart: () => Promise<void>;
  addToCart: (courseId: string) => Promise<void>;
  removeFromCart: (courseId: string) => Promise<void>;
  enroll: () => Promise<void>;
  cancelEnrollment: (courseId: string) => void;
  submitCaptcha: () => Promise<void>;
  refreshCaptcha: () => Promise<void>;
  setCaptchaInput: (value: string) => void;
  setCaptchaModal: (state: CaptchaModalState) => void;
  setUiCaptchaRequired: (required: boolean) => void;
}

/**
 * 수강신청 관련 상태와 로직을 관리하는 커스텀 훅
 * @returns {UseCoursesReturn} 수강신청 관련 상태와 함수들
 */
export function useCourses(): UseCoursesReturn {
  // 강의 관련 상태 관리
  const [courses, setCourses] = useState<Course[]>([]); // 전체 강의 목록
  const [cart, setCart] = useState<Course[]>([]); // 장바구니에 담긴 강의 목록
  const [enrolledCourses, setEnrolledCourses] = useState<Course[]>([]); // 수강신청 완료된 강의 목록

  // UI 상태 관리
  const [loading, setLoading] = useState(false); // 수강신청 진행 중 여부
  const [message, setMessage] = useState(''); // 사용자에게 보여줄 상태 메시지

  // 캡차 관련 상태 관리
  const [captchaModal, setCaptchaModal] = useState<CaptchaModalState>({ open: false }); // 캡차 모달 상태
  const [captchaInput, setCaptchaInput] = useState(''); // 사용자가 입력한 캡차 답안
  const [captchaMsg, setCaptchaMsg] = useState(''); // 캡차 검증 결과 메시지
  const [uiCaptchaRequired, setUiCaptchaRequired] = useState(false); // UI에서 캡차 요구 상태

  // 빠른 클릭 감지를 위한 ref
  const clickTimesRef = useRef<number[]>([]); // 클릭 시간들을 저장하는 배열

  /**
   * 수강취소를 처리하는 함수
   * @param {string} courseId - 취소할 강의 ID
   */
  const cancelEnrollment = (courseId: string) => {
    // 히스토리에서 해당 과목 제거
    setEnrolledCourses(prev => prev.filter(course => course.courseId !== courseId));

    // 강의 목록에서 enrolled 수를 1 감소 (프론트엔드에서만)
    setCourses(prev => prev.map(course =>
      course.courseId === courseId
        ? { ...course, enrolled: Math.max(0, course.enrolled - 1) }
        : course
    ));
  };

  /**
   * 서버 응답에 따라 캡차 모달을 열어야 하는지 확인하는 함수
   * @param {any} data - 서버 응답 데이터
   * @returns {boolean} 캡차 모달이 열렸는지 여부
   */
  const openCaptchaIfNeeded = (data: any): boolean => {
    if (uiCaptchaRequired) {
      if (!captchaModal.open) {
        // already required on UI, ensure modal is open
        refreshCaptcha();
      }
      return true;
    }
    const requireCaptcha = data?.requireCaptcha ?? data?.require_captcha;
    if (requireCaptcha) {
      const cap = data?.captcha || {};
      setCaptchaModal({
        open: true,
        captchaId: cap.captchaId || cap.captcha_id,
        audioPath: cap.audioPath || cap.audio_path
      });
      setUiCaptchaRequired(true);
      return true;
    }
    return false;
  };

  /**
   * 강의 목록을 서버에서 가져오는 함수
   */
  const fetchCourses = async () => {
    const res = await fetch('/api/courses');
    let data: any = [];
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    setCourses(Array.isArray(data) ? data : []);
  };

  /**
   * 장바구니 목록을 서버에서 가져오는 함수
   */
  const fetchCart = async () => {
    const res = await fetch('/api/cart');
    let data: any = [];
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    setCart(Array.isArray(data) ? data : []);
  };

  /**
   * 강의를 장바구니에 추가하는 함수
   * @param {string} courseId - 추가할 강의 ID
   */
  const addToCart = async (courseId: string) => {
    const res = await fetch('/api/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ courseId })
    });
    let data: any = {};
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    fetchCart();
  };

  /**
   * 장바구니에서 강의를 제거하는 함수
   * @param {string} courseId - 제거할 강의 ID
   */
  const removeFromCart = async (courseId: string) => {
    const res = await fetch(`/api/cart/${courseId}`, { method: 'DELETE' });
    let data: any = {};
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    fetchCart();
  };

  /**
   * 수강신청을 실행하는 함수
   * 장바구니에 담긴 모든 강의에 대해 신청을 진행합니다.
   */
  const enroll = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch('/api/enroll', { method: 'POST' });
      let data: any = null;
      try { data = await res.json(); } catch { }
      if (openCaptchaIfNeeded(data)) return;
      const results = data?.results || [];
      const successfulResults = results.filter((r: any) => r.success);
      const okCount = successfulResults.length;
      const failCount = results.length - okCount;

      // 신청한 모든 과목들을 enrolledCourses에 저장 (성공/실패 무관, 중복 제거)
      const enrolledCourses = cart.filter(course =>
        results.some((r: any) => r.courseId === course.courseId)
      );
      setEnrolledCourses(prev => {
        const newCourses = enrolledCourses.filter(
          course => !prev.some(enrolled => enrolled.courseId === course.courseId)
        );
        return [...prev, ...newCourses];
      });

      setMessage(formatEnrollmentResult(okCount, failCount));
      await fetchCourses();
      await fetchCart();
    } finally {
      setLoading(false);
    }
  };

  /**
   * 캡차 인증을 제출하는 함수
   * 캡차 인증 성공 시 수강신청 완료 처리를 합니다.
   */
  const submitCaptcha = async () => {
    if (!captchaModal.captchaId) return;
    setCaptchaMsg('');
    const res = await fetch('/api/enroll/unlock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ captchaId: captchaModal.captchaId, userInput: captchaInput })
    });
    const data = await res.json();
    if (data?.success) {
      setCaptchaModal({ open: false });
      setCaptchaInput('');
      setUiCaptchaRequired(false);
      clickTimesRef.current = [];

      // 현재 cart에 있는 강의들을 enrolledCourses에 추가
      setEnrolledCourses(prev => {
        const newCourses = cart.filter(
          course => !prev.some(enrolled => enrolled.courseId === course.courseId)
        );
        return [...prev, ...newCourses];
      });

      setMessage(`수강신청 완료: ${cart.length}개 과목`);
      await fetchCourses();
      await fetchCart();
    } else {
      setCaptchaMsg(data?.message || CAPTCHA_MESSAGES.VERIFICATION_FAILED);
    }
  };

  /**
   * 새로운 캡차를 생성하고 모달을 여는 함수
   */
  const refreshCaptcha = async () => {
    setCaptchaMsg('');
    setCaptchaInput('');
    const res = await fetchAfterReady('/api/captcha/generate');
    const data = await res.json();
    setCaptchaModal({ open: true, captchaId: data?.captchaId, audioPath: data?.audioPath });
  };

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchCourses();
    fetchCart();
  }, []);

  // 장바구니에 담긴 강의 ID들을 Set으로 변환 (성능 최적화)
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
    fetchCart,
    addToCart,
    removeFromCart,
    enroll,
    cancelEnrollment,
    submitCaptcha,
    refreshCaptcha,
    setCaptchaInput,
    setCaptchaModal,
    setUiCaptchaRequired,
  };
}