/**
 * SearchFilter 컴포넌트
 *
 * 강의 검색을 위한 필터링 UI를 제공합니다.
 * 학년도, 학기, 교과목 수준, 이수구분, 개설전공/학과, 키워드 등의 필터 옵션을 제공합니다.
 */

import styles from '../../../pages/courses/Courses.module.css';
import FilterGroup from './FilterGroup';
import { useFilterState, SearchParams } from '../hooks/useFilterState';

/**
 * SearchFilter 컴포넌트의 props 타입
 */
interface SearchFilterProps {
  /** 검색 실행 콜백 함수 */
  onSearch: (params: SearchParams) => void;
}

/**
 * SearchFilter 컴포넌트
 *
 * 강의 검색 및 필터링을 위한 UI를 제공합니다.
 * 필터 상태 관리는 useFilterState 훅에서, 개별 필터는 FilterGroup 컴포넌트로 렌더링합니다.
 *
 * @param props - SearchFilter 컴포넌트 props
 * @returns JSX.Element
 */
export default function SearchFilter({ onSearch }: SearchFilterProps) {
  // 필터 상태 관리 훅
  const {
    keyword,
    semester,
    year,
    level,
    category,
    department,
    departments,
    setKeyword,
    setSemester,
    setYear,
    setLevel,
    setCategory,
    setDepartment,
    buildSearchParams,
    resetFilters
  } = useFilterState();

  /**
   * 검색 실행 함수
   * 현재 필터 상태를 SearchParams로 변환하여 부모 컴포넌트에 전달합니다.
   */
  const handleSearch = () => {
    onSearch(buildSearchParams());
  };

  /**
   * 필터 초기화 함수
   * 모든 필터를 초기 상태로 되돌리고, 빈 검색 조건으로 강의 목록을 다시 불러옵니다.
   */
  const handleResetFilters = () => {
    resetFilters();
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
      {/* 필터 박스 헤더 - 안내 문구 및 초기화 버튼 */}
      <div className={styles.filterBoxHeader}>
        <div className={styles.filterGuideText}>
          원하는 조건을 선택한 후 각 필터의 조회 버튼을 눌러 강의를 검색하세요.
        </div>
        <button className={styles.resetButton} onClick={handleResetFilters}>
          필터 초기화
        </button>
      </div>

      {/* 첫 번째 필터 행 - 학년도, 학기, 교과목 수준, 이수구분, 개설전공/학과 */}
      <div className={styles.filterRow}>
        {/* 학년도 선택 (필수) */}
        <FilterGroup
          label="학년도"
          required
          type="select"
          value={year}
          onChange={setYear}
          onSearch={handleSearch}
          options={[
            { value: '', label: '전체' },
            { value: '2025', label: '2025' },
            { value: '2024', label: '2024' }
          ]}
        />

        {/* 학기 선택 (필수) */}
        <FilterGroup
          label="학기"
          required
          type="select"
          value={semester}
          onChange={setSemester}
          onSearch={handleSearch}
          options={[
            { value: '', label: '전체' },
            { value: '1', label: '1학기' },
            { value: '2', label: '2학기' }
          ]}
        />

        {/* 교과목 수준 선택 */}
        <FilterGroup
          label="교과목 수준"
          type="select"
          value={level}
          onChange={setLevel}
          onSearch={handleSearch}
          options={[
            { value: '', label: '전체' },
            { value: '학사', label: '학사' },
            { value: '석사', label: '석사' }
          ]}
        />

        {/* 이수구분 선택 */}
        <FilterGroup
          label="이수구분"
          type="select"
          value={category}
          onChange={setCategory}
          onSearch={handleSearch}
          options={[
            { value: '', label: '전체' },
            { value: '전선', label: '전선' },
            { value: '전필', label: '전필' },
            { value: '교양', label: '교양' }
          ]}
        />

        {/* 개설전공/학과 선택 (필수) */}
        <FilterGroup
          label="개설전공/학과"
          required
          type="select"
          value={department}
          onChange={setDepartment}
          onSearch={handleSearch}
          options={[
            { value: '', label: '전체' },
            ...departments.map((dept) => ({ value: dept, label: dept }))
          ]}
        />
      </div>

      {/* 두 번째 필터 행 - 교과목 키워드, 학번/성명 */}
      <div className={styles.filterRow}>
        {/* 교과목 키워드 입력 */}
        <FilterGroup
          label="교과목 키워드"
          type="input"
          value={keyword}
          onChange={setKeyword}
          onSearch={handleSearch}
          placeholder="교과목명 또는 코드"
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />

        {/* 학번/성명 입력 (필수) - 현재는 UI만 존재 */}
        <FilterGroup
          label="학번/성명"
          required
          type="input"
          value=""
          onChange={() => {}}
          onSearch={handleSearch}
          placeholder="학번 입력"
        />
      </div>
    </div>
  );
}