/**
 * 수강신청 페이지 컴포넌트
 * 강의 목록 조회, 장바구니 관리, 수강신청 기능을 제공합니다.
 * 빠른 클릭 감지를 통한 캡차 시스템과 함께 안전한 수강신청 환경을 제공합니다.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCourses } from '../../features/courses/hooks/useCourses';
import styles from './Courses.module.css';
import CoursesHeader from '../../features/courses/components/CoursesHeader';
import CoursesMainContent from '../../features/courses/components/CoursesMainContent';
import ClickDetector from '../../features/courses/components/ClickDetector';
import CaptchaModal from '../../features/courses/components/CaptchaModal';

/**
 * CoursesPage 컴포넌트 - 수강신청 메인 페이지
 * 강의 검색, 장바구니 관리, 수강신청/취소 기능을 통합적으로 제공합니다.
 * @returns {JSX.Element} 수강신청 페이지 JSX 요소
 */
export default function CoursesPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  
  // 수강신청 관련 상태와 로직을 커스텀 훅으로 관리
  const {
    courses,
    cart,
    enrolledCourses,
    cartIdSet,
    loading,
    message,
    captchaModal,
    captchaInput,
    captchaMsg,
    clickTimesRef,
    addToCart,
    removeFromCart,
    enroll,
    cancelEnrollment,
    submitCaptcha,
    refreshCaptcha,
    setCaptchaInput,
    setCaptchaModal,
    setUiCaptchaRequired,
  } = useCourses();

  /**
   * 로그아웃 처리 함수
   * 사용자를 로그아웃하고 메인 페이지로 이동합니다.
   */
  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className={styles.coursesPage}>
      {/* 수강신청 페이지 헤더 */}
      <CoursesHeader 
        cart={cart}
        loading={loading}
        onLogout={handleLogout}
        onEnroll={enroll}
      />

      {/* 메인 콘텐츠 영역 */}
      <CoursesMainContent 
        courses={courses}
        cart={cart}
        enrolledCourses={enrolledCourses}
        cartIdSet={cartIdSet}
        loading={loading}
        message={message}
        onAddToCart={addToCart}
        onRemoveFromCart={removeFromCart}
        onEnroll={enroll}
        onCancelEnrollment={cancelEnrollment}
      />

      {/* 전역 빠른 클릭 감지기 - 3초 내 5번 클릭 시 캡차 트리거 */}
      <ClickDetector
        enabled
        onTrigger={async () => {
          setUiCaptchaRequired(true);
          await refreshCaptcha();
        }}
        clickTimesRef={clickTimesRef}
      />

      {/* 캡차 인증 모달 */}
      <CaptchaModal 
        captchaModal={captchaModal}
        captchaInput={captchaInput}
        captchaMsg={captchaMsg}
        onInputChange={setCaptchaInput}
        onSubmit={submitCaptcha}
        onRefresh={refreshCaptcha}
        onClose={() => setCaptchaModal({ open: false })}
      />
    </div>
  );
}
