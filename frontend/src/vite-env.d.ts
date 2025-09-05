/**
 * Vite 환경 타입 선언 파일
 * Vite 관련 타입들과 모듈 선언을 정의합니다.
 */

/// <reference types="vite/client" />

/**
 * JPG 이미지 파일을 모듈로 사용할 수 있도록 선언
 * 이미지 파일을 import하면 문자열(URL)을 반환합니다.
 */
declare module '*.jpg' {
  const src: string;
  export default src;
}

/**
 * PNG 이미지 파일을 모듈로 사용할 수 있도록 선언
 * 이미지 파일을 import하면 문자열(URL)을 반환합니다.
 */
declare module '*.png' {
  const src: string;
  export default src;
}

/**
 * CSS 모듈을 사용할 수 있도록 선언
 * CSS 모듈을 import하면 클래스명이 매핑된 객체를 반환합니다.
 */
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

