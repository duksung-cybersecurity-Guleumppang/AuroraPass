/**
 * 검색 필터 컴포넌트
 * 강의 검색을 위한 필터링 옵션들을 제공합니다.
 * 학년도, 학기, 학번/성명, 교과목 수준, 이수구분, 전공/학과 등의 필터링 옵션을 제공합니다.
 */

import React from 'react';
import styles from '../../../pages/courses/Courses.module.css';

/**
 * SearchFilter 컴포넌트 - 강의 검색 및 필터링을 위한 UI 제공
 * @returns {JSX.Element} 검색 필터 컴포넌트
 */
export default function SearchFilter() {
  return (
    <div className={styles.searchFilterBox}>
      {/* 첫 번째 필터 행: 기본 검색 조건들 */}
      <div className={styles.filterRow}>
        {/* 학년도 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>학년도 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect}>
            <option value="2024">2024</option>
          </select>
        </div>
        
        {/* 학기 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>학기 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect}>
            <option value="1">1학기</option>
            <option value="2">2학기</option>
          </select>
        </div>
        
        {/* 학번 입력 및 조회 (필수) */}
        <div className={styles.filterGroup}>
          <label>학번/성명 <span className={styles.required}>*</span></label>
          <input type="text" className={styles.filterInput} placeholder="학번 입력" />
          <button className={styles.searchButton}>조회</button>
        </div>
        
        {/* 성명 입력 및 조회 */}
        <div className={styles.filterGroup}>
          <input type="text" className={styles.filterInput} placeholder="성명 입력" />
          <button className={styles.searchButton}>조회</button>
        </div>
      </div>
      
      {/* 두 번째 필터 행: 세부 검색 조건들 */}
      <div className={styles.filterRow}>
        {/* 교과목 수준 선택 (선택사항) */}
        <div className={styles.filterGroup}>
          <label>교과목 수준</label>
          <select className={styles.filterSelect}>
            <option value="">전체</option>
            <option value="학사">학사</option>
            <option value="석사">석사</option>
          </select>
        </div>
        
        {/* 이수구분 선택 (선택사항) */}
        <div className={styles.filterGroup}>
          <label>이수구분</label>
          <select className={styles.filterSelect}>
            <option value="">전체</option>
            <option value="전선">전선</option>
            <option value="전필">전필</option>
            <option value="교양">교양</option>
          </select>
        </div>
        
        {/* 검색 타입 선택 라디오 버튼 그룹 */}
        <div className={styles.radioGroup}>
          <input type="radio" id="전공학과선택" name="searchType" defaultChecked />
          <label htmlFor="전공학과선택">전공/학과선택</label>
          <input type="radio" id="영역구분" name="searchType" />
          <label htmlFor="영역구분">영역구분</label>
          <input type="radio" id="교과목검색" name="searchType" />
          <label htmlFor="교과목검색">교과목검색</label>
        </div>
        
        {/* 개설전공/학과 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>개설전공/학과 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect}>
            <option value="">선택하세요</option>
            <option value="컴퓨터공학과">컴퓨터공학과</option>
            <option value="전자공학과">전자공학과</option>
          </select>
        </div>
      </div>
    </div>
  );
}