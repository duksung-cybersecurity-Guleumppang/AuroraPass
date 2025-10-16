/**
 * useCoursesData 커스텀 훅
 *
 * 강의, 장바구니, 수강 목록 등의 데이터 조회 및 상태 관리를 담당합니다.
 */

import { useEffect, useState } from 'react';
import { Course } from '../../../shared/types/courses';
import {
  fetchCoursesApi,
  searchCoursesApi,
  fetchCartApi,
  fetchMyCoursesApi
} from './useCoursesApi';

/**
 * useCoursesData 훅의 반환 타입
 */
export interface UseCoursesDataReturn {
  // === 데이터 상태 ===
  courses: Course[];
  cart: Course[];
  enrolledCourses: Course[];

  // === 상태 업데이트 함수 ===
  setCourses: React.Dispatch<React.SetStateAction<Course[]>>;
  setCart: React.Dispatch<React.SetStateAction<Course[]>>;
  setEnrolledCourses: React.Dispatch<React.SetStateAction<Course[]>>;

  // === 데이터 조회 함수 ===
  fetchCourses: (options?: { suppressCaptcha?: boolean }) => Promise<any>;
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
  }) => Promise<any>;
  fetchCart: (options?: { suppressCaptcha?: boolean }) => Promise<any>;
  fetchMyCourses: (options?: { suppressCaptcha?: boolean }) => Promise<any>;
}

/**
 * useCoursesData 커스텀 훅
 *
 * 강의, 장바구니, 수강 목록의 데이터 조회와 상태 관리를 담당합니다.
 * CAPTCHA 처리는 호출하는 쪽에서 담당합니다.
 *
 * @returns {UseCoursesDataReturn} 데이터 상태와 조회 함수들
 */
export function useCoursesData(): UseCoursesDataReturn {
  // === 데이터 상태 ===
  const [courses, setCourses] = useState<Course[]>([]);
  const [cart, setCart] = useState<Course[]>([]);
  const [enrolledCourses, setEnrolledCourses] = useState<Course[]>([]);

  /**
   * 전체 강의 목록을 서버에서 가져오는 함수
   *
   * @param options - 옵션 객체
   * @param options.suppressCaptcha - CAPTCHA 확인을 건너뛸지 여부
   * @returns 서버 응답 데이터
   */
  const fetchCourses = async (options?: { suppressCaptcha?: boolean }) => {
    const data = await fetchCoursesApi();
    // CAPTCHA 체크는 호출하는 쪽에서 하도록 데이터 반환
    if (options?.suppressCaptcha || !data?.requireCaptcha) {
      setCourses(Array.isArray(data) ? data : []);
    }
    return data;
  };

  /**
   * 검색 조건에 맞는 강의 목록을 조회하는 함수
   *
   * @param params - 검색 조건 객체
   * @returns 서버 응답 데이터
   */
  const searchCourses = async (params?: {
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
  }) => {
    const data = await searchCoursesApi(params);
    // CAPTCHA 체크는 호출하는 쪽에서 하도록 데이터 반환
    if (!data?.requireCaptcha) {
      setCourses(Array.isArray(data) ? data : []);
    }
    return data;
  };

  /**
   * 장바구니 목록을 서버에서 가져오는 함수
   *
   * @param options - 옵션 객체
   * @param options.suppressCaptcha - CAPTCHA 확인을 건너뛸지 여부
   * @returns 서버 응답 데이터
   */
  const fetchCart = async (options?: { suppressCaptcha?: boolean }) => {
    const data = await fetchCartApi();
    if (options?.suppressCaptcha || !data?.requireCaptcha) {
      setCart(Array.isArray(data) ? data : []);
    }
    return data;
  };

  /**
   * 수강신청한 강의 목록을 서버에서 가져오는 함수
   *
   * @param options - 옵션 객체
   * @param options.suppressCaptcha - CAPTCHA 확인을 건너뛸지 여부
   * @returns 서버 응답 데이터
   */
  const fetchMyCourses = async (options?: { suppressCaptcha?: boolean }) => {
    const data = await fetchMyCoursesApi();
    if (options?.suppressCaptcha || !data?.requireCaptcha) {
      setEnrolledCourses(Array.isArray(data) ? data : []);
    }
    return data;
  };

  /**
   * 컴포넌트 마운트 시 초기 데이터 로드
   * CAPTCHA 모달이 바로 뜨지 않도록 suppressCaptcha 옵션 사용
   */
  useEffect(() => {
    const suppress = { suppressCaptcha: true };
    fetchCourses(suppress);
    fetchCart(suppress);
    fetchMyCourses(suppress);
  }, []);

  return {
    // 상태
    courses,
    cart,
    enrolledCourses,

    // 상태 업데이트 함수
    setCourses,
    setCart,
    setEnrolledCourses,

    // 데이터 조회 함수
    fetchCourses,
    searchCourses,
    fetchCart,
    fetchMyCourses
  };
}
