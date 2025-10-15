/**
 * 수강신청 성공한 과목 목록 컴포넌트
 * 수강신청에 성공한 강의 목록을 표시합니다.
 * 사용자가 현재 수강신청한 과목들을 확인하고 수강취소 기능을 제공합니다.
 */

import React from 'react';
import { Course } from '../../../shared/types/courses';
import styles from '../../../pages/courses/Courses.module.css';
import enrolledCoursesStyles from './EnrolledCourses.module.css';
import { COURSE_DEFAULTS, ENROLLMENT_MESSAGES } from '../../../shared/constants/courses';

/**
 * EnrolledCourses 컴포넌트의 props 인터페이스
 * @interface EnrolledCoursesProps
 * @property {Course[]} enrolledCourses - 수강신청에 성공한 강의 목록 배열
 * @property {(courseId: string) => void} onCancelEnrollment - 수강취소 시 실행될 콜백 함수
 */
interface EnrolledCoursesProps {
  enrolledCourses: Course[];
  onCancelEnrollment: (courseId: string) => void;
}

/**
 * EnrolledCourses 컴포넌트 - 수강신청한 과목 목록 표시 및 취소 기능 제공
 * @param {EnrolledCoursesProps} props - EnrolledCourses 컴포넌트에 전달되는 props
 * @returns {JSX.Element} 수강신청한 과목 목록 컴포넌트
 */
export default function EnrolledCourses({ enrolledCourses, onCancelEnrollment }: EnrolledCoursesProps) {

  return (
    <section>
      {/* 수강 목록 헤더 */}
      <div className={styles.coursesListHeader}>
        <div>
          <div className={styles.coursesListTitle}>수강 목록</div>
          <div className={styles.coursesListSubtitle}>수강신청한 과목을 확인하고 취소할 수 있습니다.</div>
        </div>
      </div>

      {/* 수강신청한 과목 테이블 */}
      <div className={styles.coursesTable}>
        <table className={`${styles.table} ${enrolledCoursesStyles.enrolledTable}`}>
          {/* 테이블 헤더 */}
          <thead>
            <tr>
              <th className={enrolledCoursesStyles.colYear}>학년도</th>
              <th className={enrolledCoursesStyles.colSemester}>학기</th>
              <th className={enrolledCoursesStyles.colTitle}>강의명</th>
              <th className={enrolledCoursesStyles.colCode}>강의코드</th>
              <th className={enrolledCoursesStyles.colProfessor}>교수명</th>
              <th className={enrolledCoursesStyles.colCredit}>학점</th>
              <th className={enrolledCoursesStyles.colLevel}>교과목 수준</th>
              <th className={enrolledCoursesStyles.colCategory}>이수구분</th>
              <th className={enrolledCoursesStyles.colSchedule}>시간표</th>
              <th className={enrolledCoursesStyles.colCapacity}>정원</th>
              <th className={enrolledCoursesStyles.colButton}>수강취소</th>
            </tr>
          </thead>
          <tbody>
            {enrolledCourses.length === 0 ? (
              // 수강신청한 과목이 없을 때 표시되는 메시지
              <tr>
                <td colSpan={11} className={enrolledCoursesStyles.emptyMessage}>
                  {ENROLLMENT_MESSAGES.NO_ENROLLED}
                </td>
              </tr>
            ) : (
              // 수강신청한 각 과목을 테이블 행으로 렌더링
              enrolledCourses.map((c) => (
                <tr key={c.courseId}>
                  <td className={enrolledCoursesStyles.colYear}>{COURSE_DEFAULTS.ACADEMIC_YEAR}</td>
                  <td className={enrolledCoursesStyles.colSemester}>{COURSE_DEFAULTS.SEMESTER}</td>
                  <td className={enrolledCoursesStyles.colTitle} title={c.title}>{c.title}</td>
                  <td className={enrolledCoursesStyles.colCode}>{c.courseId}</td>
                  <td className={enrolledCoursesStyles.colProfessor} title={c.professor}>{c.professor}</td>
                  <td className={enrolledCoursesStyles.colCredit}>{COURSE_DEFAULTS.DEFAULT_CREDITS}</td>
                  <td className={enrolledCoursesStyles.colLevel}>{COURSE_DEFAULTS.COURSE_LEVEL}</td>
                  <td className={enrolledCoursesStyles.colCategory}>{COURSE_DEFAULTS.COURSE_TYPE}</td>
                  <td className={enrolledCoursesStyles.colSchedule} title={c.schedule}>{c.schedule}</td>
                  <td className={enrolledCoursesStyles.colCapacity}>{c.enrolled}/{c.capacity}</td>
                  <td className={enrolledCoursesStyles.colButton}>
                    {/* 수강취소 버튼 */}
                    <button
                      onClick={() => onCancelEnrollment(c.courseId)}
                      className={`${styles.buttonBase} ${styles.removeButton}`}
                    >
                      수강취소
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}