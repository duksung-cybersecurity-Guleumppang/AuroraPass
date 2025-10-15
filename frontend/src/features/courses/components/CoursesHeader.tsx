/**
 * 수강신청 페이지 헤더 컴포넌트
 * 페이지 제목, 장바구니 개수, 로그아웃 및 수강신청 버튼을 표시합니다.
 */

import React from 'react';
import { Course } from '../../../shared/types/courses';
import styles from '../../../pages/courses/Courses.module.css';
import { formatCartCount, getButtonText } from '../../../shared/utils/messages';
import { ENROLLMENT_MESSAGES } from '../../../shared/constants/courses';

/**
 * CoursesHeader 컴포넌트의 props 인터페이스
 * @interface CoursesHeaderProps
 * @property {Course[]} cart - 장바구니에 담긴 강의 목록
 * @property {boolean} loading - 수강신청 진행 중 여부
 * @property {() => void} onLogout - 로그아웃 버튼 클릭 시 실행될 콜백 함수
 * @property {() => void} onEnroll - 수강신청 버튼 클릭 시 실행될 콜백 함수
 */
interface CoursesHeaderProps {
  cart: Course[];
  loading: boolean;
  onLogout: () => void;
  onEnroll: () => void;
}

/**
 * CoursesHeader 컴포넌트 - 수강신청 페이지의 헤더 영역
 * @param {CoursesHeaderProps} props - CoursesHeader 컴포넌트에 전달되는 props
 * @returns {JSX.Element} 수강신청 페이지 헤더 컴포넌트
 */
export default function CoursesHeader({ cart, loading, onLogout, onEnroll }: CoursesHeaderProps) {
  return (
    <header className={styles.coursesHeader}>
      <div className={styles.headerTitleSection}>
        <h1 className={styles.headerTitle}>수강신청</h1>
      </div>
      <div className={styles.headerActions}>
        {/* 로그아웃 버튼 */}
        <button
          onClick={onLogout}
          className={`${styles.buttonBase} ${styles.logoutButton}`}
        >
          로그아웃
        </button>
      </div>
    </header>
  );
}