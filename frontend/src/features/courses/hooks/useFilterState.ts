/**
 * useFilterState 커스텀 훅
 *
 * 검색 필터의 상태 관리 및 학과 목록 로딩 로직을 캡슐화합니다.
 * SearchFilter 컴포넌트에서 사용되는 모든 필터 상태를 관리합니다.
 */

import { useEffect, useState } from 'react';

/**
 * 검색 파라미터 타입 정의
 */
export type SearchParams = {
  keyword?: string;
  year?: number;
  semester?: number;
  level?: string;
  category?: string;
  department?: string;
  page?: number;
  pageSize?: number;
  sort?: 'recent' | 'name' | 'code';
  order?: 'asc' | 'desc';
};

/**
 * useFilterState 훅의 반환 타입
 */
export interface UseFilterStateReturn {
  // === 필터 상태 ===
  keyword: string;
  semester: string;
  year: string;
  level: string;
  category: string;
  department: string;
  searchType: 'dept' | 'area' | 'keyword';
  departments: string[];

  // === 상태 업데이트 함수 ===
  setKeyword: (value: string) => void;
  setSemester: (value: string) => void;
  setYear: (value: string) => void;
  setLevel: (value: string) => void;
  setCategory: (value: string) => void;
  setDepartment: (value: string) => void;
  setSearchType: (value: 'dept' | 'area' | 'keyword') => void;

  // === 유틸리티 함수 ===
  buildSearchParams: () => SearchParams;
  resetFilters: () => void;
}

/**
 * useFilterState 커스텀 훅
 *
 * 검색 필터의 모든 상태를 관리하고, 학과 목록을 자동으로 로딩합니다.
 * 학년도와 학기가 변경되면 해당 조건에 맞는 학과 목록을 다시 불러옵니다.
 *
 * @returns {UseFilterStateReturn} 필터 상태와 관련 함수들
 */
export function useFilterState(): UseFilterStateReturn {
  // === 필터 상태 ===
  const [keyword, setKeyword] = useState('');
  const [semester, setSemester] = useState('');
  const [year, setYear] = useState('');
  const [level, setLevel] = useState('');
  const [category, setCategory] = useState('');
  const [department, setDepartment] = useState('');
  const [searchType, setSearchType] = useState<'dept' | 'area' | 'keyword'>('dept');
  const [departments, setDepartments] = useState<string[]>([]);

  /**
   * 학년도와 학기가 변경될 때마다 학과 목록을 서버에서 가져옵니다.
   *
   * 동작 순서:
   * 1. 학년도/학기를 쿼리 파라미터로 구성
   * 2. GET /api/departments API 호출
   * 3. 학과 목록 상태 업데이트
   * 4. 현재 선택된 학과가 새 목록에 없으면 초기화
   */
  useEffect(() => {
    let aborted = false;

    (async () => {
      try {
        // 쿼리 파라미터 구성
        const params = new URLSearchParams();
        if (year) params.set('year', year);
        if (semester) params.set('semester', semester);

        // 학과 목록 API 호출
        const res = await fetch(`/api/departments?${params.toString()}`);
        const data = await res.json();

        // 컴포넌트가 언마운트되지 않았으면 상태 업데이트
        if (!aborted && Array.isArray(data)) {
          setDepartments(data);

          // 현재 선택된 department가 새 목록에 없으면 초기화
          if (department && !data.includes(department)) {
            setDepartment('');
          }
        }
      } catch (error) {
        // 네트워크 오류 등 예외 상황 무시
        console.error('[useFilterState] 학과 목록 로딩 실패:', error);
      }
    })();

    // cleanup: 컴포넌트 언마운트 시 요청 취소
    return () => {
      aborted = true;
    };
  }, [year, semester]); // year, semester가 변경될 때마다 실행

  /**
   * 현재 필터 상태를 SearchParams 객체로 변환합니다.
   *
   * 빈 값은 undefined로 설정하여 API 요청 시 제외됩니다.
   *
   * @returns {SearchParams} 검색 파라미터 객체
   */
  const buildSearchParams = (): SearchParams => {
    return {
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
    };
  };

  /**
   * 모든 필터를 초기 상태로 되돌립니다.
   */
  const resetFilters = () => {
    setKeyword('');
    setSemester('');
    setYear('');
    setLevel('');
    setCategory('');
    setDepartment('');
    setSearchType('dept');
  };

  // 모든 상태와 함수 반환
  return {
    // 상태
    keyword,
    semester,
    year,
    level,
    category,
    department,
    searchType,
    departments,

    // 상태 업데이트 함수
    setKeyword,
    setSemester,
    setYear,
    setLevel,
    setCategory,
    setDepartment,
    setSearchType,

    // 유틸리티 함수
    buildSearchParams,
    resetFilters
  };
}
