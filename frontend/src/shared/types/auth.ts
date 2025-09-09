/**
 * 인증 컨텍스트 관련 타입 정의
 * 사용자 인증 상태 관리를 위한 컨텍스트 타입들을 정의합니다.
 */

import React from 'react';

/**
 * 인증 컨텍스트에서 제공하는 값들의 타입
 * @interface AuthContextType
 * @property {boolean} isAuthenticated - 현재 사용자의 인증 상태
 * @property {function} login - 로그인 함수 (사용자명, 비밀번호를 받아 로그인 성공 여부를 반환)
 * @property {function} logout - 로그아웃 함수
 * @property {boolean} loading - 인증 상태 확인 중 여부
 */
export interface AuthContextType {
    isAuthenticated: boolean;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
    loading: boolean;
}

/**
 * AuthProvider 컴포넌트의 props 타입
 * @interface AuthProviderProps
 * @property {React.ReactNode} children - AuthProvider 내부에 렌더링될 자식 컴포넌트들
 */
export interface AuthProviderProps {
    children: React.ReactNode;
}