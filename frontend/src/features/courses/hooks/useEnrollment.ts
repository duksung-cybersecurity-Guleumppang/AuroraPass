/**
 * useEnrollment 커스텀 훅
 *
 * 수강신청, 수강취소, 개별 수강신청 로직을 담당합니다.
 */

import { Course } from '../../../shared/types/courses';
import { formatEnrollmentResult } from '../../../shared/utils/messages';
import { addToCartApi, enrollApi, cancelEnrollmentApi } from './useCoursesApi';

/**
 * useEnrollment 훅의 파라미터 타입
 */
export interface UseEnrollmentParams {
  /** 전체 강의 목록 */
  courses: Course[];
  /** 장바구니 목록 */
  cart: Course[];
  /** 강의 목록 업데이트 함수 */
  setCourses: React.Dispatch<React.SetStateAction<Course[]>>;
  /** 수강 목록 업데이트 함수 */
  setEnrolledCourses: React.Dispatch<React.SetStateAction<Course[]>>;
  /** 로딩 상태 업데이트 함수 */
  setLoading: (loading: boolean) => void;
  /** 메시지 업데이트 함수 */
  setMessage: (message: string) => void;
  /** CAPTCHA 확인 함수 */
  openCaptchaIfNeeded: (data: any) => boolean;
  /** 강의 목록 새로고침 함수 */
  fetchCourses: () => Promise<void>;
  /** 장바구니 새로고침 함수 */
  fetchCart: () => Promise<void>;
  /** 수강 목록 새로고침 함수 */
  fetchMyCourses: () => Promise<void>;
}

/**
 * useEnrollment 훅의 반환 타입
 */
export interface UseEnrollmentReturn {
  /** 장바구니의 모든 강의를 수강신청 */
  enroll: () => Promise<void>;
  /** 개별 강의를 바로 수강신청 */
  enrollSingle: (courseId: string) => Promise<void>;
  /** 수강신청 취소 */
  cancelEnrollment: (courseId: string) => Promise<void>;
}

/**
 * useEnrollment 커스텀 훅
 *
 * 수강신청 관련 로직을 캡슐화합니다.
 * - 장바구니 일괄 수강신청
 * - 개별 강의 바로 수강신청
 * - 수강신청 취소
 *
 * @param params - 훅 파라미터
 * @returns {UseEnrollmentReturn} 수강신청 관련 함수들
 */
export function useEnrollment({
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
}: UseEnrollmentParams): UseEnrollmentReturn {
  /**
   * 장바구니의 모든 강의를 수강신청하는 함수
   *
   * 동작 순서:
   * 1. 현재 스크롤 위치 저장
   * 2. POST /api/enroll 호출하여 장바구니의 모든 강의 신청
   * 3. 성공/실패 결과를 받아서 처리
   * 4. 성공한 강의는 수강 목록에 추가
   * 5. 결과 메시지 표시
   * 6. 데이터 새로고침
   * 7. 스크롤 위치 복원
   */
  const enroll = async () => {
    const scrollY = window.scrollY;
    setLoading(true);
    setMessage('');

    try {
      const data = await enrollApi();
      if (openCaptchaIfNeeded(data)) return;

      const results = data?.results || [];
      const successfulResults = results.filter((r: any) => r.success);
      const okCount = successfulResults.length;
      const failCount = results.length - okCount;

      // 성공한 강의들을 수강 목록에 추가
      const enrolledCourses = cart
        .filter(course => results.some((r: any) => r.courseId === course.courseId))
        .map(course => ({ ...course, enrolled: (course.enrolled ?? 0) + 1 }));

      setEnrolledCourses(prev => {
        const newCourses = enrolledCourses.filter(
          course => !prev.some(enrolled => enrolled.courseId === course.courseId)
        );
        return [...prev, ...newCourses];
      });

      setMessage(formatEnrollmentResult(okCount, failCount));

      // 데이터 새로고침
      await fetchCourses();
      await fetchCart();
      await fetchMyCourses();

      // 스크롤 위치 복원
      requestAnimationFrame(() => {
        window.scrollTo(0, scrollY);
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * 개별 강의를 바로 수강신청하는 함수
   *
   * 장바구니를 거치지 않고 임시로 추가한 후 바로 수강신청합니다.
   *
   * @param {string} courseId - 수강신청할 강의 ID
   */
  const enrollSingle = async (courseId: string) => {
    const scrollY = window.scrollY;
    setLoading(true);
    setMessage('');

    try {
      // 1. 임시로 장바구니에 추가
      const addData = await addToCartApi(courseId);
      if (openCaptchaIfNeeded(addData)) return;

      // 2. 즉시 수강신청 실행
      const data = await enrollApi();
      if (openCaptchaIfNeeded(data)) return;

      const results = data?.results || [];
      const targetResult = results.find((r: any) => r.courseId === courseId);

      if (targetResult?.success) {
        const enrolledCourse = courses.find(c => c.courseId === courseId);
        if (enrolledCourse) {
          setEnrolledCourses(prev => {
            if (prev.some(c => c.courseId === courseId)) return prev;
            return [...prev, { ...enrolledCourse, enrolled: (enrolledCourse.enrolled ?? 0) + 1 }];
          });
        }
        setMessage('수강신청이 완료되었습니다.');
      } else {
        setMessage(targetResult?.message || '수강신청에 실패했습니다.');
      }

      // 데이터 새로고침
      await fetchCourses();
      await fetchCart();
      await fetchMyCourses();

      // 스크롤 위치 복원
      requestAnimationFrame(() => {
        window.scrollTo(0, scrollY);
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * 수강신청을 취소하는 함수
   *
   * @param {string} courseId - 취소할 강의 ID
   */
  const cancelEnrollment = async (courseId: string) => {
    try {
      const data = await cancelEnrollmentApi(courseId);

      if (openCaptchaIfNeeded(data)) return;

      if (data?.success) {
        // 수강 목록에서 제거
        setEnrolledCourses(prev => prev.filter(course => course.courseId !== courseId));

        // 강의 목록에서 enrolled 수 감소
        setCourses(prev => prev.map(course =>
          course.courseId === courseId
            ? { ...course, enrolled: Math.max(0, course.enrolled - 1) }
            : course
        ));

        setMessage('수강취소가 완료되었습니다.');

        // 데이터 새로고침
        await fetchCourses();
        await fetchMyCourses();
      } else {
        setMessage(data?.message || '수강취소에 실패했습니다.');
      }
    } catch (error) {
      console.error('[cancelEnrollment] 예외 오류:', error);
      setMessage('수강취소 중 오류가 발생했습니다.');
    }
  };

  return {
    enroll,
    enrollSingle,
    cancelEnrollment
  };
}
