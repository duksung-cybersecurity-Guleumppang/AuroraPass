/**
 * 수강신청 관련 API 호출 함수들 (Re-export)
 *
 * 이 파일은 카테고리별로 분리된 API 함수들을 하나의 진입점으로 모아서 제공합니다.
 * 기존 import 경로 호환성을 유지하기 위한 파일입니다.
 *
 * API 카테고리:
 * - coursesApi: 강의 조회 관련 API
 * - cartApi: 장바구니 관련 API
 * - enrollmentApi: 수강신청 관련 API
 */

// 강의 조회 API
export { fetchCoursesApi, searchCoursesApi, fetchMyCoursesApi } from '../api/coursesApi';
export type { SearchCoursesParams } from '../api/coursesApi';

// 장바구니 API
export { fetchCartApi, addToCartApi, removeFromCartApi } from '../api/cartApi';

// 수강신청 API
export { enrollApi, cancelEnrollmentApi, submitCaptchaApi } from '../api/enrollmentApi';
