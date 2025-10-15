/**
 * 검색 필터 컴포넌트
 * 강의 검색을 위한 필터링 옵션들을 제공합니다.
 * 학년도, 학기, 학번/성명, 교과목 수준, 이수구분, 전공/학과 등의 필터링 옵션을 제공합니다.
 */

import React, { useEffect, useState } from 'react';
import styles from '../../../pages/courses/Courses.module.css';

/**
 * SearchFilter 컴포넌트 - 강의 검색 및 필터링을 위한 UI 제공
 * @returns {JSX.Element} 검색 필터 컴포넌트
 */
type SearchParams = { keyword?: string; year?: number; semester?: number; level?: string; category?: string; department?: string; page?: number; pageSize?: number; sort?: 'recent' | 'name' | 'code'; order?: 'asc' | 'desc' };

export default function SearchFilter({ onSearch }: { onSearch: (params: SearchParams) => void; }) {
  const [keyword, setKeyword] = useState('');
  const [semester, setSemester] = useState('');
  const [year, setYear] = useState('');
  const [level, setLevel] = useState('');
  const [category, setCategory] = useState('');
  const [department, setDepartment] = useState('');
  const [searchType, setSearchType] = useState<'dept' | 'area' | 'keyword'>('dept');
  const [departments, setDepartments] = useState<string[]>([]);

  useEffect(() => {
    let aborted = false;
    (async () => {
      try {
        const params = new URLSearchParams();
        if (year) params.set('year', year);
        if (semester) params.set('semester', semester);
        const res = await fetch(`/api/departments?${params.toString()}`);
        const data = await res.json();
        if (!aborted && Array.isArray(data)) {
          setDepartments(data);
          // 현재 선택된 department가 목록에 없으면 초기화
          if (department && !data.includes(department)) setDepartment('');
        }
      } catch { }
    })();
    return () => { aborted = true; };
  }, [year, semester]);

  const handleSearch = async () => {
    onSearch({
      keyword: keyword.trim() || undefined,
      year: Number(year) || undefined,
      semester: Number(semester) || undefined,
      level: level || undefined,
      category: category || undefined,
      department: department || undefined,
      page: 1,
      pageSize: 50,
      sort: 'recent',
      order: 'desc'
    });
  };

  // 필터 초기화 함수
  const handleResetFilters = () => {
    setKeyword('');
    setSemester('');
    setYear('');
    setLevel('');
    setCategory('');
    setDepartment('');
    setSearchType('dept');
    // 필터 초기화 시 강의 목록도 초기화
    onSearch({
      keyword: undefined,
      year: undefined,
      semester: undefined,
      level: undefined,
      category: undefined,
      department: undefined,
      page: 1,
      pageSize: 50,
      sort: 'recent',
      order: 'desc'
    });
  };


  return (
    <div className={styles.searchFilterBox}>
      {/* 필터 박스 헤더 - 필터 초기화 버튼 */}
      <div className={styles.filterBoxHeader}>
        <div className={styles.filterGuideText}>
          원하는 조건을 선택한 후 각 필터의 조회 버튼을 눌러 강의를 검색하세요.
        </div>
        <button className={styles.resetButton} onClick={handleResetFilters}>필터 초기화</button>
      </div>

      {/* 첫 번째 필터 행 */}
      <div className={styles.filterRow}>
        {/* 학년도 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>학년도 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect} value={year} onChange={e => setYear(e.target.value)}>
            <option value="">전체</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
          </select>
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>

        {/* 학기 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>학기 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect} value={semester} onChange={e => setSemester(e.target.value)}>
            <option value="">전체</option>
            <option value="1">1학기</option>
            <option value="2">2학기</option>
          </select>
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>

        {/* 교과목 수준 선택 (선택사항) */}
        <div className={styles.filterGroup}>
          <label>교과목 수준</label>
          <select className={styles.filterSelect} value={level} onChange={e => setLevel(e.target.value)}>
            <option value="">전체</option>
            <option value="학사">학사</option>
            <option value="석사">석사</option>
          </select>
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>

        {/* 이수구분 선택 (선택사항) */}
        <div className={styles.filterGroup}>
          <label>이수구분</label>
          <select className={styles.filterSelect} value={category} onChange={e => setCategory(e.target.value)}>
            <option value="">전체</option>
            <option value="전선">전선</option>
            <option value="전필">전필</option>
            <option value="교양">교양</option>
          </select>
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>

        {/* 개설전공/학과 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>개설전공/학과 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect} value={department} onChange={e => setDepartment(e.target.value)}>
            <option value="">전체</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>
      </div>

      {/* 두 번째 필터 행 */}
      <div className={styles.filterRow}>
        {/* 교과목 키워드 입력 및 조회 */}
        <div className={styles.filterGroup}>
          <label>교과목 키워드</label>
          <input
            type="text"
            className={styles.filterInput}
            placeholder="교과목명 또는 코드"
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>

        {/* 학번 입력 및 조회 (필수) */}
        <div className={styles.filterGroup}>
          <label>학번/성명 <span className={styles.required}>*</span></label>
          <input type="text" className={styles.filterInput} placeholder="학번 입력" />
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>
      </div>
    </div>
  );
}