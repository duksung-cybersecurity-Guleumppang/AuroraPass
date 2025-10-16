/**
 * 수강신청 관련 API 함수들
 *
 * 수강신청, 수강취소, CAPTCHA 인증 등의 API 호출을 담당합니다.
 */

/**
 * 장바구니의 모든 강의를 수강신청하는 함수
 *
 * POST /api/enroll 엔드포인트를 호출합니다.
 *
 * @returns {Promise<any>} 서버 응답 데이터 (수강신청 결과 또는 CAPTCHA 요구)
 */
export async function enrollApi(): Promise<any> {
  const res = await fetch('/api/enroll', { method: 'POST' });

  let data: any = null;
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 null 반환 */
  }
  return data;
}

/**
 * 수강신청을 취소하는 함수
 *
 * DELETE /api/enroll/{courseId} 엔드포인트를 호출합니다.
 *
 * @param {string} courseId - 취소할 강의 ID
 * @returns {Promise<any>} 서버 응답 데이터 (성공 여부 또는 CAPTCHA 요구)
 */
export async function cancelEnrollmentApi(courseId: string): Promise<any> {
  const res = await fetch(`/api/enroll/${courseId}`, { method: 'DELETE' });

  let data: any = {};
  try {
    data = await res.json();
  } catch {
    /* JSON 파싱 실패 시 빈 객체 반환 */
  }
  return data;
}

/**
 * CAPTCHA 인증을 제출하는 함수
 *
 * POST /api/enroll/unlock 엔드포인트를 호출합니다.
 *
 * @param {string} captchaId - CAPTCHA ID
 * @param {string} userInput - 사용자가 입력한 CAPTCHA 답
 * @returns {Promise<any>} 서버 응답 데이터 (인증 성공 여부)
 */
export async function submitCaptchaApi(captchaId: string, userInput: string): Promise<any> {
  const res = await fetch('/api/enroll/unlock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ captchaId, userInput })
  });

  return await res.json();
}
