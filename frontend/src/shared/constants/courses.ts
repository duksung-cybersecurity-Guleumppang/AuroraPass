/**
 * 수강신청 관련 상수 정의
 * 하드코딩된 값들과 기본값들을 정의합니다.
 */

/**
 * 수강신청 기본 정보
 * @constant {object} COURSE_DEFAULTS
 * @property {string} ACADEMIC_YEAR - 기본 학년도
 * @property {string} SEMESTER - 기본 학기
 * @property {number} DEFAULT_CREDITS - 기본 학점
 * @property {string} COURSE_LEVEL - 기본 교과목 수준
 * @property {string} COURSE_TYPE - 기본 이수구분
 * @property {string} DEPARTMENT - 기본 학과
 * @property {string} CLASS_NUMBER - 기본 분반
 * @property {number} THEORY_HOURS - 기본 이론 시간
 * @property {number} PRACTICE_HOURS - 기본 실습 시간
 */
export const COURSE_DEFAULTS = {
  ACADEMIC_YEAR: '2024',
  SEMESTER: '1학기',
  DEFAULT_CREDITS: 3,
  COURSE_LEVEL: '학사',
  COURSE_TYPE: '전선',
  DEPARTMENT: '컴퓨터공학과',
  CLASS_NUMBER: '01',
  THEORY_HOURS: 3,
  PRACTICE_HOURS: 0,
} as const;

/**
 * 수강신청 상태 메시지
 * @constant {object} ENROLLMENT_MESSAGES
 * @property {string} LOADING - 로딩 중 메시지
 * @property {string} SUCCESS_FORMAT - 성공 메시지 형식
 * @property {string} EMPTY_CART - 빈 장바구니 메시지
 * @property {string} NO_ENROLLED - 수강신청한 과목 없음 메시지
 */
export const ENROLLMENT_MESSAGES = {
  LOADING: '신청 중…',
  SUCCESS_FORMAT: '신청 완료: 성공 {success}건, 실패 {fail}건',
  EMPTY_CART: '담긴 과목이 없습니다.',
  NO_ENROLLED: '수강신청한 과목이 없습니다.',
} as const;