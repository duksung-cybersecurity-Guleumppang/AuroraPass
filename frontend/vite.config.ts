/**
 * Vite 설정 파일
 * React 애플리케이션의 개발 서버 설정과 빌드 설정을 정의합니다.
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

/**
 * Vite 설정 객체
 * - React SWC 플러그인을 사용하여 빠른 개발 환경 제공
 * - 개발 서버의 포트 설정 (환경변수 우선, 기본값 3000)
 * - API 및 정적 파일에 대한 프록시 설정으로 백엔드와 통신
 */
export default defineConfig({
  plugins: [react()], // React SWC 플러그인 사용 (빠른 개발 서버와 HMR 제공)
  server: {
    // 개발 서버 포트 설정 (환경변수 FRONT_PORT > PORT > 기본값 3000)
    port: Number(process.env.FRONT_PORT || process.env.PORT || 3000),
    host: true, // 모든 네트워크 인터페이스에서 접근 가능하도록 설정
    proxy: {
      // API 요청을 백엔드 서버로 프록시 (CORS 문제 해결)
      '/api': { 
        target: `http://backend:${process.env.BACKEND_PORT || process.env.PORT || 8000}`, 
        changeOrigin: true 
      },
      // 정적 파일 요청을 백엔드 서버로 프록시
      '/static': { 
        target: `http://backend:${process.env.BACKEND_PORT || process.env.PORT || 8000}`, 
        changeOrigin: true 
      },
    },
  },
});


