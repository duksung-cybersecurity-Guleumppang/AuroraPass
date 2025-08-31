/**
 * 수강신청 페이지 유틸리티 함수들
 * 색상 상수와 스타일 객체를 정의합니다.
 */

/**
 * 애플리케이션에서 사용하는 색상 팔레트
 */
export const colors = {
    bg: '#f6f8fb',
    surface: '#ffffff',
    text: '#0f172a',
    subText: '#64748b',
    border: '#e2e8f0',
    primary: '#2563eb',
    primaryHover: '#1d4ed8',
    danger: '#ef4444',
    dangerHover: '#dc2626'
} as const;

/**
 * 버튼의 기본 스타일 객체
 */
export const buttonBase: React.CSSProperties = {
    padding: '10px 14px',
    borderRadius: 10,
    border: '1px solid transparent',
    fontWeight: 600,
    cursor: 'pointer'
};