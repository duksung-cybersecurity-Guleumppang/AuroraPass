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
 * @property {(courseId: string) => void} onEnrollSingle - 개별 강의를 수강신청할 때 실행될 콜백 함수
 */
interface CoursesTableProps {
  courses: Course[];
  cartIdSet: Set<string>;
  onAddToCart: (courseId: string) => void;
  onEnrollSingle: (courseId: string) => void;
}

/**
 * CoursesTable 컴포넌트 - 강의 목록을 테이블로 표시하고 선택 기능을 제공
 * @param {CoursesTableProps} props - CoursesTable 컴포넌트에 전달되는 props
 * @returns {JSX.Element} 강의 목록 테이블 컴포넌트
 */
export default function CoursesTable({ courses, cartIdSet, onAddToCart, onEnrollSingle }: CoursesTableProps) {
  return (
    <div className={`${styles.coursesTable} ${styles.scrollable}`}>
      <table className={styles.table}>
        {/* 테이블 헤더 - 각 컬럼의 제목을 정의 */}
        <thead>
          <tr>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colCheckbox}`}>장바구니</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colButton}`}>수강신청</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colCategory}`}>이수구분</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colDepartment}`}>개설전공/학과</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colCode}`}>교과목코드</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colTitle}`}>교과목명</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colClass}`}>분반</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colLevel}`}>교과목수준</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colCredit}`}>학점</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colTheory}`}>이론</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colPractice}`}>실습</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colCapacity}`}>신청/정원</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colProfessor}`}>담당교수</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colSchedule}`}>시간표</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colYear}`}>학년도</th>
            <th className={`${coursesTableStyles.tableHeader} ${coursesTableStyles.colSemester}`}>학기</th>
          </tr>
        </thead>
        <tbody>
          {/* 각 강의 정보를 테이블 행으로 렌더링 */}
          {courses.map((c) => {
            // 현재 강의가 장바구니에 있는지 확인
            const inCart = cartIdSet.has(c.courseId);
            // 정원이 가득 찬 경우
            const isFull = c.enrolled >= c.capacity;

            return (
              <tr key={c.courseId}>
                <td className={coursesTableStyles.colCheckbox}>
                  {/* 장바구니 추가를 위한 체크박스 */}
                  <input
                    type="checkbox"
                    checked={inCart}
                    onChange={() => onAddToCart(c.courseId)}
                    disabled={isFull}
                  />
                </td>
                <td className={coursesTableStyles.colButton}>
                  {/* 개별 수강신청 버튼 */}
                  <button
                    onClick={() => onEnrollSingle(c.courseId)}
                    disabled={isFull}
                    className={`${styles.buttonBase} ${isFull ? coursesTableStyles.enrollButtonDisabled : coursesTableStyles.enrollButton}`}
                  >
                    {isFull ? '마감' : '수강신청'}
                  </button>
                </td>
                {/* 강의 정보 표시 - 서버 값 우선, 없으면 기본값 */}
                <td className={coursesTableStyles.colCategory}>{c.category || COURSE_DEFAULTS.COURSE_TYPE}</td>
                <td className={coursesTableStyles.colDepartment} title={c.department ?? ''}>{c.department ?? ''}</td>
                <td className={coursesTableStyles.colCode}>{c.courseId}</td>
                <td className={coursesTableStyles.colTitle} title={c.title}>{c.title}</td>
                <td className={coursesTableStyles.colClass}>{COURSE_DEFAULTS.CLASS_NUMBER}</td>
                <td className={coursesTableStyles.colLevel}>{c.level || COURSE_DEFAULTS.COURSE_LEVEL}</td>
                <td className={coursesTableStyles.colCredit}>{COURSE_DEFAULTS.DEFAULT_CREDITS}</td>
                <td className={coursesTableStyles.colTheory}>{c.theoryHours ?? COURSE_DEFAULTS.THEORY_HOURS}</td>
                <td className={coursesTableStyles.colPractice}>{c.practiceHours ?? COURSE_DEFAULTS.PRACTICE_HOURS}</td>
                <td className={coursesTableStyles.colCapacity}>{c.enrolled}/{c.capacity}</td>
                <td className={coursesTableStyles.colProfessor} title={c.professor}>{c.professor}</td>
                <td className={coursesTableStyles.colSchedule} title={c.schedule}>{c.schedule}</td>
                <td className={coursesTableStyles.colYear}>{c.year ?? ''}</td>
                <td className={coursesTableStyles.colSemester}>{c.semester ?? ''}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}