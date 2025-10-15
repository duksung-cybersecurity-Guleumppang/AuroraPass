/**
 * 장바구니 컴포넌트
 * 장바구니에 담긴 강의 목록과 수강신청 기능을 제공합니다.
 * 사용자가 선택한 강의들을 한번에 관리하고 일괄 수강신청할 수 있는 기능을 제공합니다.
 */

import React from 'react';
import { Course } from '../../../shared/types/courses';
import styles from '../../../pages/courses/Courses.module.css';
import { COURSE_DEFAULTS, ENROLLMENT_MESSAGES } from '../../../shared/constants/courses';
import { getButtonText } from '../../../shared/utils/messages';

/**
 * Cart 컴포넌트의 props 인터페이스
 * @interface CartProps
 * @property {Course[]} cart - 장바구니에 담긴 강의 목록 배열
 * @property {boolean} loading - 수강신청 진행 상태 (로딩 중인지 여부)
 * @property {string} message - 사용자에게 보여줄 상태 메시지 (성공/오류 등)
 * @property {() => void} onEnroll - 수강신청 버튼 클릭 시 실행될 콜백 함수
 * @property {(courseId: string) => void} onRemoveFromCart - 장바구니에서 특정 강의 제거 시 실행될 콜백 함수
 */
interface CartProps {
  cart: Course[];
  loading: boolean;
  message: string;
  onEnroll: () => void;
  onRemoveFromCart: (courseId: string) => void;
}

/**
 * Cart 컴포넌트 - 장바구니 기능을 제공하는 사이드바
 * @param {CartProps} props - Cart 컴포넌트에 전달되는 props
 * @returns {JSX.Element} 장바구니 사이드바 컴포넌트
 */
export default function Cart({ cart, loading, message, onEnroll, onRemoveFromCart }: CartProps) {
  return (
    <aside className={styles.cartSidebar}>
      <div className={styles.cartContainer}>
        {/* 장바구니 헤더 영역 - 제목과 설명을 표시 */}
        <div className={styles.coursesListHeader}>
          <div>
            <div className={styles.coursesListTitle}>수강과목 내역</div>
            <div className={styles.coursesListSubtitle}>선택한 강의를 확인하고 일괄 수강신청할 수 있습니다.</div>
          </div>
        </div>
        
        {/* 장바구니 컨텐츠 영역 */}
        <div className={styles.cartContent}>
          {cart.length === 0 ? (
            // 장바구니가 비어있을 때 표시되는 메시지
            <div className={styles.cartEmpty}>{ENROLLMENT_MESSAGES.EMPTY_CART}</div>
          ) : (
            // 장바구니에 강의가 있을 때 표시되는 테이블
            <div className={styles.coursesTable}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>학년도</th>
                    <th>학기</th>
                    <th>강의명</th>
                    <th>강의코드</th>
                    <th>교수명</th>
                    <th>학점</th>
                    <th>교과목 수준</th>
                    <th>이수구분</th>
                    <th>시간표</th>
                    <th>정원</th>
                    <th>제거</th>
                  </tr>
                </thead>
                <tbody>
                  {/* 장바구니의 각 강의를 렌더링 */}
                  {cart.map((c) => (
                    <tr key={c.courseId}>
                      <td>{COURSE_DEFAULTS.ACADEMIC_YEAR}</td>
                      <td>{COURSE_DEFAULTS.SEMESTER}</td>
                      <td className={styles.courseTitle}>{c.title}</td>
                      <td className={styles.courseId}>{c.courseId}</td>
                      <td className={styles.courseProfessor}>{c.professor}</td>
                      <td>{COURSE_DEFAULTS.DEFAULT_CREDITS}</td>
                      <td>{COURSE_DEFAULTS.COURSE_LEVEL}</td>
                      <td>{COURSE_DEFAULTS.COURSE_TYPE}</td>
                      <td className={styles.courseSchedule}>{c.schedule}</td>
                      <td className={styles.courseCapacity}>{c.enrolled}/{c.capacity}</td>
                      <td>
                        {/* 강의 제거 버튼 */}
                        <button
                          onClick={() => onRemoveFromCart(c.courseId)}
                          className={`${styles.buttonBase} ${styles.removeButton}`}
                        >
                          제거
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 일괄 수강신청 버튼 - 로딩 중이거나 장바구니가 비어있으면 비활성화 */}
        <button
          onClick={onEnroll}
          disabled={loading || cart.length === 0}
          className={`${styles.buttonBase} ${styles.enrollButton} ${styles.cartEnrollButton} ${(loading || cart.length === 0) ? styles.enrollButtonDisabled : ''}`}
        >
          {getButtonText(loading, '수강신청', ENROLLMENT_MESSAGES.LOADING)}
        </button>
      </div>
    </aside>
  );
}