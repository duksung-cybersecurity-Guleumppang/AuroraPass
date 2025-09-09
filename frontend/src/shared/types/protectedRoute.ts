/**
 * ProtectedRoute 컴포넌트의 타입 정의
 * 인증이 필요한 라우트를 보호하기 위한 컴포넌트의 props 타입을 정의합니다.
 */

import React from 'react';

/**
 * ProtectedRoute 컴포넌트의 props 인터페이스
 * @interface ProtectedRouteProps
 * @property {React.ReactNode} children - 보호된 라우트 내부에 렌더링될 자식 컴포넌트들
 */
export interface ProtectedRouteProps {
    children: React.ReactNode;
}