/**
 * 수강신청 페이지 메인 콘텐츠 컴포넌트
 * 검색 필터, 강의 목록 테이블, 장바구니, 수강신청 완료 목록을 표시합니다.
 */

import React from 'react';
import { Course } from '../../../shared/types/courses';
import styles from '../../../pages/courses/Courses.module.css';
import SearchFilter from './SearchFilter';
import CoursesTable from './CoursesTable';
import Cart from './Cart';
import EnrolledCourses from './EnrolledCourses';

/**
 * CoursesMainContent 컴포넌트의 props 인터페이스
 * @interface CoursesMainContentProps
 * @property {Course[]} courses - 전체 강의 목록
 * @property {Course[]} cart - 장바구니에 담긴 강의 목록
 * @property {Course[]} enrolledCourses - 수강신청 완료된 강의 목록
 * @property {Set<string>} cartIdSet - 장바구니 강의 ID들의 Set
 * @property {boolean} loading - 수강신청 진행 중 여부
 * @property {string} message - 상태 메시지
 * @property {(courseId: string) => void} onAddToCart - 장바구니 추가 함수
 * @property {(courseId: string) => void} onRemoveFromCart - 장바구니 제거 함수
 * @property {() => void} onEnroll - 수강신청 함수
 * @property {(courseId: string) => void} onCancelEnrollment - 수강취소 함수
 * @property {(courseId: string) => void} onEnrollSingle - 개별 수강신청 함수
 */
interface CoursesMainContentProps {
  courses: Course[];
  cart: Course[];
  enrolledCourses: Course[];
  cartIdSet: Set<string>;
  loading: boolean;
  message: string;
  onAddToCart: (courseId: string) => void;
  onRemoveFromCart: (courseId: string) => void;
  onEnroll: () => void;
  onCancelEnrollment: (courseId: string) => void;
  onSearch: (params: { keyword?: string; year?: number; semester?: number; level?: string; category?: string; department?: string; page?: number; pageSize?: number; sort?: 'recent' | 'name' | 'code'; order?: 'asc' | 'desc' }) => void;
  onEnrollSingle: (courseId: string) => void;
}

/**
 * CoursesMainContent 컴포넌트 - 수강신청 페이지의 메인 콘텐츠 영역
 * @param {CoursesMainContentProps} props - CoursesMainContent 컴포넌트에 전달되는 props
 * @returns {JSX.Element} 수강신청 페이지 메인 콘텐츠 컴포넌트
 */
export default function CoursesMainContent({
  courses,
  cart,
  enrolledCourses,
  cartIdSet,
  loading,
  message,
  onAddToCart,
  onRemoveFromCart,
  onEnroll,
  onCancelEnrollment,
  onSearch,
  onEnrollSingle,
}: CoursesMainContentProps) {
  return (
    <div className={styles.coursesContent}>
      <section>
        {/* 강의 검색 필터 헤더 */}
        <div className={styles.coursesListHeader}>
          <div>
            <div className={styles.coursesListTitle}>강의 검색</div>
            <div className={styles.coursesListSubtitle}>학년도, 학기, 전공/학과를 선택하여 강의를 검색하세요.</div>
          </div>
        </div>

        {/* 강의 검색 필터 */}
        <SearchFilter onSearch={onSearch} />

        {/* 개설과목 목록 헤더 */}
        <div className={styles.coursesListHeader} style={{ marginTop: '24px' }}>
          <div>
            <div className={styles.coursesListTitle}>개설과목 목록</div>
            <div className={styles.coursesListSubtitle}>정원/시간표 확인 후 체크박스로 선택하여 수강신청하세요.</div>
          </div>
        </div>

        {/* 강의 목록 테이블 */}
        <CoursesTable
          courses={courses}
          cartIdSet={cartIdSet}
          onAddToCart={onAddToCart}
          onEnrollSingle={onEnrollSingle}
        />
      </section>

      {/* 장바구니 사이드바 */}
      <Cart
        cart={cart}
        loading={loading}
        message={message}
        onEnroll={onEnroll}
        onRemoveFromCart={onRemoveFromCart}
      />

      {/* 수강신청 완료된 과목 목록 */}
      <EnrolledCourses
        enrolledCourses={enrolledCourses}
        onCancelEnrollment={onCancelEnrollment}
      />
    </div>
  );
}