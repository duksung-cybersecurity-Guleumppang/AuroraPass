/**
 * 강의 목록 테이블 컴포넌트
 * 강의 목록을 테이블 형태로 표시하고 장바구니 추가 기능을 제공합니다.
 * 사용자가 수강 가능한 강의들을 확인하고 선택할 수 있는 기능을 제공합니다.
 */

import React from 'react';
import { Course } from '../../../shared/types/courses';
import styles from '../../../pages/courses/Courses.module.css';
import coursesTableStyles from './CoursesTable.module.css';
import { COURSE_DEFAULTS } from '../../../shared/constants/courses';

/**
 * CoursesTable 컴포넌트의 props 인터페이스
 * @interface CoursesTableProps
 * @property {Course[]} courses - 표시할 강의 목록 배열
 * @property {Set<string>} cartIdSet - 현재 장바구니에 담긴 강의 ID들의 Set (중복 방지 및 빠른 검색용)
 * @property {(courseId: string) => void} onAddToCart - 강의를 장바구니에 추가할 때 실행될 콜백 함수
 */
interface CoursesTableProps {
  courses: Course[];
  cartIdSet: Set<string>;
  onAddToCart: (courseId: string) => void;
}

/**
 * CoursesTable 컴포넌트 - 강의 목록을 테이블로 표시하고 선택 기능을 제공
 * @param {CoursesTableProps} props - CoursesTable 컴포넌트에 전달되는 props
 * @returns {JSX.Element} 강의 목록 테이블 컴포넌트
 */
export default function CoursesTable({ courses, cartIdSet, onAddToCart }: CoursesTableProps) {
  return (
    <div className={styles.coursesTable}>
      <table className={styles.table}>
        {/* 테이블 헤더 - 각 컬럼의 제목을 정의 */}
        <thead>
          <tr>
            <th className={coursesTableStyles.tableHeader}>선택</th>
            <th className={coursesTableStyles.tableHeader}>수강신청</th>
            <th className={coursesTableStyles.tableHeader}>이수구분</th>
            <th className={coursesTableStyles.tableHeader}>개설전공/학과</th>
            <th className={coursesTableStyles.tableHeader}>교과목코드</th>
            <th className={coursesTableStyles.tableHeader}>교과목명</th>
            <th className={coursesTableStyles.tableHeader}>분반</th>
            <th className={coursesTableStyles.tableHeader}>교과목수준</th>
            <th className={coursesTableStyles.tableHeader}>학점</th>
            <th className={coursesTableStyles.tableHeader}>이론</th>
            <th className={coursesTableStyles.tableHeader}>실습</th>
            <th className={coursesTableStyles.tableHeader}>신청/정원</th>
            <th className={coursesTableStyles.tableHeader}>담당교수</th>
            <th className={coursesTableStyles.tableHeader}>시간표</th>
          </tr>
        </thead>
        <tbody>
          {/* 각 강의 정보를 테이블 행으로 렌더링 */}
          {courses.map((c) => {
            // 현재 강의가 장바구니에 있는지 확인
            const inCart = cartIdSet.has(c.courseId);
            // 버튼 비활성화 조건: 이미 장바구니에 있거나 정원이 가득 찬 경우
            const disabled = inCart || c.enrolled >= c.capacity;
            
            return (
              <tr key={c.courseId}>
                <td>
                  {/* 강의 선택을 위한 체크박스 */}
                  <input 
                    type="checkbox" 
                    checked={inCart}
                    onChange={() => !disabled && onAddToCart(c.courseId)}
                    disabled={disabled && !inCart}
                  />
                </td>
                <td>
                  {/* 수강신청 버튼 - 장바구니에 강의를 추가 */}
                  <button
                    onClick={() => onAddToCart(c.courseId)}
                    disabled={disabled}
                    className={`${styles.buttonBase} ${disabled ? coursesTableStyles.enrollButtonDisabled : coursesTableStyles.enrollButton}`}
                  >
                    {inCart ? '수강신청' : '수강신청'}
                  </button>
                </td>
                {/* 강의 정보 표시 - 상수와 동적 값들 */}
                <td>{COURSE_DEFAULTS.COURSE_TYPE}</td>
                <td>{COURSE_DEFAULTS.DEPARTMENT}</td>
                <td className={styles.courseId}>{c.courseId}</td>
                <td className={styles.courseTitle}>{c.title}</td>
                <td>{COURSE_DEFAULTS.CLASS_NUMBER}</td>
                <td>{COURSE_DEFAULTS.COURSE_LEVEL}</td>
                <td>{COURSE_DEFAULTS.DEFAULT_CREDITS}</td>
                <td>{COURSE_DEFAULTS.THEORY_HOURS}</td>
                <td>{COURSE_DEFAULTS.PRACTICE_HOURS}</td>
                <td className={styles.courseCapacity}>{c.enrolled}/{c.capacity}</td>
                <td className={styles.courseProfessor}>{c.professor}</td>
                <td className={styles.courseSchedule}>{c.schedule}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}