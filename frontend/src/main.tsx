/**
 * 애플리케이션 진입점
 * React 애플리케이션을 DOM에 마운트하는 메인 파일입니다.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// 전역 CSS 변수와 공통 스타일 import
import './shared/styles/variables.css';
import './shared/styles/common.css';

/**
 * React 애플리케이션을 root DOM 엘리먼트에 렌더링
 * React.StrictMode로 감싸서 개발 모드에서 추가적인 검사와 경고를 활성화합니다.
 */
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

