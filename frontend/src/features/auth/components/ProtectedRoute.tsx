/**
 * 인증이 필요한 라우트를 보호하는 컴포넌트
 * 사용자가 로그인하지 않은 경우 메인 페이지로 리디렉션합니다.
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { ProtectedRouteProps } from '../../../shared/types/protectedRoute';
import styles from './ProtectedRoute.module.css';

/**
 * 보호된 라우트 컴포넌트
 * @param {ProtectedRouteProps} props - 컴포넌트 props
 * @param {React.ReactNode} props.children - 보호된 라우트 내부에 렌더링될 자식 요소들
 * @returns {JSX.Element} 인증 상태에 따른 적절한 JSX 요소
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, loading } = useAuth();

    // 인증 상태 확인 중일 때 로딩 화면 표시
    if (loading) {
        return (
            <div className={styles.loadingContainer}>
                로딩 중...
            </div>
        );
    }

    // 인증되지 않은 사용자는 메인 페이지로 리디렉션
    if (!isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    // 인증된 사용자에게는 자식 컴포넌트들을 렌더링
    return <>{children}</>;
}
