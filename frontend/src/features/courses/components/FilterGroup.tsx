/**
 * FilterGroup 컴포넌트
 *
 * 검색 필터의 개별 필터 그룹을 렌더링하는 재사용 가능한 컴포넌트
 * select 또는 input 타입의 필터를 지원하며, 조회 버튼과 함께 표시됩니다.
 */

import React from 'react';
import styles from '../../../pages/courses/Courses.module.css';

/**
 * FilterGroup 컴포넌트의 props 타입 정의
 */
interface FilterGroupProps {
  /** 필터 레이블 텍스트 */
  label: string;
  /** 필수 입력 필드 여부 */
  required?: boolean;
  /** 필터 타입 (select 드롭다운 또는 input 텍스트) */
  type: 'select' | 'input';
  /** 현재 선택된 값 */
  value: string;
  /** 값 변경 핸들러 */
  onChange: (value: string) => void;
  /** 조회 버튼 클릭 핸들러 */
  onSearch: () => void;
  /** select 타입일 때의 옵션 목록 */
  options?: Array<{ value: string; label: string }>;
  /** input 타입일 때의 placeholder */
  placeholder?: string;
  /** Enter 키 입력 핸들러 (input 타입에서만 사용) */
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}

/**
 * FilterGroup 컴포넌트
 *
 * 레이블, 입력 필드(select 또는 input), 조회 버튼으로 구성된 필터 그룹
 *
 * @param props - FilterGroup 컴포넌트 props
 * @returns JSX.Element
 */
export default function FilterGroup({
  label,
  required = false,
  type,
  value,
  onChange,
  onSearch,
  options = [],
  placeholder = '',
  onKeyDown
}: FilterGroupProps) {
  return (
    <div className={styles.filterGroup}>
      {/* 필터 레이블 (필수 표시 포함) */}
      <label>
        {label}
        {required && <span className={styles.required}> *</span>}
      </label>

      {/* select 드롭다운 타입 */}
      {type === 'select' && (
        <select
          className={styles.filterSelect}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}

      {/* input 텍스트 타입 */}
      {type === 'input' && (
        <input
          type="text"
          className={styles.filterInput}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
        />
      )}

      {/* 조회 버튼 */}
      <button className={styles.searchButton} onClick={onSearch}>
        조회
      </button>
    </div>
  );
}
