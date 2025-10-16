/**
 * 장바구니 관련 API 함수들
 *
 * 장바구니 조회, 추가, 제거 등의 API 호출을 담당합니다.
 */

/**
 * 장바구니 목록을 서버에서 가져오는 함수
 *
 * GET /api/cart 엔드포인트를 호출합니다.
 *
 * @returns {Promise<any>} 서버 응답 데이터 (장바구니 강의 목록 또는 CAPTCHA 요구)
 */
export async function fetchCartApi(): Promise<any> {
  const res = await fetch('/api/cart');
  let data: any = [];
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 배열 반환 */
  }
  return data;
}

/**
 * 강의를 장바구니에 추가하는 함수
 *
 * POST /api/cart 엔드포인트를 호출합니다.
 *
 * @param {string} courseId - 추가할 강의 ID
 * @returns {Promise<any>} 서버 응답 데이터 (성공 여부 또는 CAPTCHA 요구)
 */
export async function addToCartApi(courseId: string): Promise<any> {
  const res = await fetch('/api/cart', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ courseId })
  });

  let data: any = {};
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 객체 반환 */
  }
  return data;
}

/**
 * 장바구니에서 강의를 제거하는 함수
 *
 * DELETE /api/cart/{courseId} 엔드포인트를 호출합니다.
 *
 * @param {string} courseId - 제거할 강의 ID
 * @returns {Promise<any>} 서버 응답 데이터 (성공 여부 또는 CAPTCHA 요구)
 */
export async function removeFromCartApi(courseId: string): Promise<any> {
  const res = await fetch(`/api/cart/${courseId}`, { method: 'DELETE' });

  let data: any = {};
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 객체 반환 */
  }
  return data;
}
