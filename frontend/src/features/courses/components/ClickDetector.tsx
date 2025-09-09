/**
 * 빠른 클릭을 감지하여 캡차를 트리거하는 컴포넌트
 * 3초 내에 5번 이상 클릭하면 캡차 인증을 요구합니다.
 */

import { useEffect } from 'react';
import { ClickDetectorProps } from '../../../shared/types/courses';
import { CLICK_DETECTION } from '../../../shared/constants/captcha';

/**
 * ClickDetector 컴포넌트 - 빠른 클릭 감지 및 캡차 트리거
 * @param {ClickDetectorProps} props - ClickDetector 컴포넌트에 전달되는 props
 * @returns {null} 렌더링되지 않는 컴포넌트 (이벤트 리스너만 등록)
 */
export default function ClickDetector({ enabled, onTrigger, clickTimesRef }: ClickDetectorProps) {
  useEffect(() => {
    if (!enabled) return;
    
    /**
     * 클릭 이벤트 핸들러
     * 3초 윈도우 내의 클릭 횟수를 추적하고 임계값 도달 시 캡차를 트리거합니다.
     */
    const handler = () => {
      const now = Date.now();
      
      // 설정된 시간 윈도우 내의 클릭만 필터링
      const filtered = clickTimesRef.current.filter((t) => now - t < CLICK_DETECTION.WINDOW_MS);
      filtered.push(now);
      clickTimesRef.current = filtered;
      
      // 임계값 도달 시 캡차 트리거
      if (filtered.length >= CLICK_DETECTION.THRESHOLD) {
        clickTimesRef.current = [];
        onTrigger();
      }
    };
    
    // 전체 문서에 클릭 이벤트 리스너 등록
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  }, [enabled, onTrigger, clickTimesRef]);
  
  return null;
}