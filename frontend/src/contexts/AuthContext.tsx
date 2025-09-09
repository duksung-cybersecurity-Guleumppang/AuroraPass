/**
 * 사용자 인증 상태를 관리하는 React Context
 * 애플리케이션 전반에서 로그인/로그아웃 상태와 관련 기능을 제공합니다.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { AuthContextType, AuthProviderProps } from '../shared/types/auth';

// 인증 컨텍스트 생성
const AuthContext = createContext<AuthContextType | null>(null);

/**
 * 인증 상태를 제공하는 Provider 컴포넌트
 * @param {AuthProviderProps} props - 컴포넌트 props
 * @param {React.ReactNode} props.children - Provider 내부에 렌더링될 자식 컴포넌트들
 * @returns {JSX.Element} AuthContext.Provider로 감싼 자식 컴포넌트들
 */
export function AuthProvider({ children }: AuthProviderProps) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    // 컴포넌트 마운트 시 로그인 상태 확인
    useEffect(() => {
        checkAuthStatus();
    }, []);

    /**
     * 로컬스토리지에서 인증 상태를 확인하는 함수
     */
    const checkAuthStatus = async () => {
        try {
            // 로컬스토리지에서 로그인 상태 확인
            const isLoggedIn = localStorage.getItem('isAuthenticated') === 'true';
            setIsAuthenticated(isLoggedIn);
        } catch {
            setIsAuthenticated(false);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 사용자 로그인을 처리하는 함수
     * @param {string} username - 사용자명
     * @param {string} password - 비밀번호
     * @returns {Promise<boolean>} 로그인 성공 여부
     */
    const login = async (username: string, password: string): Promise<boolean> => {
        try {
            const response = await fetch('/api/users/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // 로그인 성공 시 로컬스토리지에 저장
                    localStorage.setItem('isAuthenticated', 'true');
                    localStorage.setItem('username', username);
                    setIsAuthenticated(true);
                    return true;
                }
            }
            return false;
        } catch {
            return false;
        }
    };

    /**
     * 사용자 로그아웃을 처리하는 함수
     * 로컬스토리지에서 인증 정보를 제거하고 상태를 업데이트합니다.
     */
    const logout = () => {
        // 로컬스토리지에서 인증 정보 제거
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('username');
        setIsAuthenticated(false);
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * AuthContext를 사용하기 위한 커스텀 훅
 * @throws {Error} AuthProvider 외부에서 사용할 경우 에러 발생
 * @returns {AuthContextType} 인증 컨텍스트 값들
 */
export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
