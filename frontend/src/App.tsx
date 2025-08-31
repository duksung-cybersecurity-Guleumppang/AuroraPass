/**
 * 메인 애플리케이션 컴포넌트
 * 라우팅과 인증 컨텍스트를 제공하는 최상위 컴포넌트입니다.
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/Login';
import CoursesPage from './pages/Courses';

/**
 * 애플리케이션의 메인 라우팅 구조를 정의하는 컴포넌트
 * @returns {JSX.Element} 전체 애플리케이션 라우팅 구조
 */
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* 메인 로그인 페이지 */}
          <Route path="/" element={<LoginPage />} />
          {/* 보호된 수강신청 페이지 */}
          <Route
            path="/courses"
            element={
              <ProtectedRoute>
                <CoursesPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}


