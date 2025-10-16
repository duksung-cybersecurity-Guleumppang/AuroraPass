/**
 * 강의 조회 관련 API 함수들
 *
 * 강의 목록 조회, 검색, 수강 목록 조회 등의 API 호출을 담당합니다.
 */

/**
 * 강의 목록 조회 파라미터 타입
 */
export interface SearchCoursesParams {
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
}

/**
 * 전체 강의 목록을 서버에서 가져오는 함수
 *
 * GET /api/courses 엔드포인트를 호출합니다.
 *
 * @returns {Promise<any>} 서버 응답 데이터 (강의 목록 배열 또는 CAPTCHA 요구)
 */
export async function fetchCoursesApi(): Promise<any> {
  const res = await fetch('/api/courses');
  let data: any = [];
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 배열 반환 */
  }
  return data;
}

/**
 * 검색 조건에 맞는 강의 목록을 조회하는 함수
 *
 * GET /api/courses?{params} 엔드포인트를 호출합니다.
 *
 * @param {SearchCoursesParams} params - 검색 조건 객체
 * @returns {Promise<any>} 서버 응답 데이터 (강의 목록 배열 또는 CAPTCHA 요구)
 */
export async function searchCoursesApi(params?: SearchCoursesParams): Promise<any> {
  // URL 쿼리 파라미터 구성
  const q = new URLSearchParams();
  if (params?.keyword) q.set('keyword', params.keyword);
  if (params?.year !== undefined) q.set('year', String(params.year));
  if (params?.semester !== undefined) q.set('semester', String(params.semester));
  if (params?.level) q.set('level', params.level);
  if (params?.category) q.set('category', params.category);
  if (params?.department) q.set('department', params.department);
  if (params?.page) q.set('page', String(params.page));
  if (params?.pageSize) q.set('pageSize', String(params.pageSize));
  if (params?.sort) q.set('sort', params.sort);
  if (params?.order) q.set('order', params.order);

  // 쿼리 스트링 생성
  const qs = q.toString();

  // 검색 API 호출
  const res = await fetch(`/api/courses${qs ? `?${qs}` : ''}`);

  // 응답 데이터 파싱
  let data: any = [];
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 배열 반환 */
  }
  return data;
}

/**
 * 수강신청한 강의 목록을 서버에서 가져오는 함수
 *
 * GET /api/my-courses 엔드포인트를 호출합니다.
 *
 * @returns {Promise<any>} 서버 응답 데이터 (수강 목록 또는 CAPTCHA 요구)
 */
export async function fetchMyCoursesApi(): Promise<any> {
  const res = await fetch('/api/my-courses');
  let data: any = [];
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 배열 반환 */
  }
  return data;
}
