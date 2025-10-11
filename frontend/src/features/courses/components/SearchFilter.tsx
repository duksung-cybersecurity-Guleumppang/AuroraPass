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
  const [semester, setSemester] = useState('1');
  const [year, setYear] = useState('2025');
  const [level, setLevel] = useState('');
  const [category, setCategory] = useState('');
  const [department, setDepartment] = useState('');
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
      pageSize: 100,
      sort: 'recent',
      order: 'desc'
    });
  };
  return (
    <div className={styles.searchFilterBox}>
      {/* 첫 번째 필터 행: 기본 검색 조건들 */}
      <div className={styles.filterRow}>
        {/* 학년도 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>학년도 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect} value={year} onChange={e => setYear(e.target.value)}>
            <option value="">전체</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
          </select>
        </div>

        {/* 학기 선택 (필수) */}
        <div className={styles.filterGroup}>
          <label>학기 <span className={styles.required}>*</span></label>
          <select className={styles.filterSelect} value={semester} onChange={e => setSemester(e.target.value)}>
            <option value="">전체</option>
            <option value="1">1학기</option>
            <option value="2">2학기</option>
          </select>
        </div>

        {/* 학번 입력 및 조회 (필수) */}
        <div className={styles.filterGroup}>
          <label>학번/성명 <span className={styles.required}>*</span></label>
          <input type="text" className={styles.filterInput} placeholder="학번 입력" />
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>

        {/* 성명 입력 및 조회 */}
        <div className={styles.filterGroup}>
          <input type="text" className={styles.filterInput} placeholder="교과목 키워드" value={keyword} onChange={e => setKeyword(e.target.value)} />
          <button className={styles.searchButton} onClick={handleSearch}>조회</button>
        </div>
      </div>

      {/* 두 번째 필터 행: 세부 검색 조건들 */}
      <div className={styles.filterRow}>
        {/* 교과목 수준 선택 (선택사항) */}
        <div className={styles.filterGroup}>
          <label>교과목 수준</label>
          <select className={styles.filterSelect} value={level} onChange={e => setLevel(e.target.value)}>
            <option value="">전체</option>
            <option value="학사">학사</option>
            <option value="석사">석사</option>
          </select>
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
          <select className={styles.filterSelect} value={department} onChange={e => setDepartment(e.target.value)}>
            <option value="">전체</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}