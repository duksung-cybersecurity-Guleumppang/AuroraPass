/**
 * 수강신청 페이지 컴포넌트
 * 강의 목록 조회, 장바구니 관리, 수강신청 기능을 제공합니다.
 */

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Course, CaptchaModalState, ClickDetectorProps } from './Courses.types';
import styles from './Courses.module.css';

/**
 * 수강신청 메인 페이지 컴포넌트
 * @returns {JSX.Element} 수강신청 페이지 JSX
 */
export default function CoursesPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  
  // 상태 관리
  const [courses, setCourses] = useState<Course[]>([]);
  const [cart, setCart] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [captchaModal, setCaptchaModal] = useState<CaptchaModalState>({ open: false });
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaMsg, setCaptchaMsg] = useState('');
  const [uiCaptchaRequired, setUiCaptchaRequired] = useState(false);
  const clickTimesRef = useRef<number[]>([]);

  /**
   * 로그아웃 처리 함수
   * 사용자를 로그아웃하고 메인 페이지로 이동합니다.
   */
  const handleLogout = () => {
    logout();
    navigate('/');
  };

  /**
   * 서버 응답에 따라 캡차 모달을 열어야 하는지 확인하는 함수
   * @param {any} data - 서버 응답 데이터
   * @returns {boolean} 캡차 모달이 열렸는지 여부
   */
  const openCaptchaIfNeeded = (data: any): boolean => {
    if (uiCaptchaRequired) {
      if (!captchaModal.open) {
        // already required on UI, ensure modal is open
        refreshCaptcha();
      }
      return true;
    }
    const requireCaptcha = data?.requireCaptcha ?? data?.require_captcha;
    if (requireCaptcha) {
      const cap = data?.captcha || {};
      setCaptchaModal({
        open: true,
        captchaId: cap.captchaId || cap.captcha_id,
        audioPath: cap.audioPath || cap.audio_path
      });
      setUiCaptchaRequired(true);
      return true;
    }
    return false;
  };

  /**
   * 강의 목록을 서버에서 가져오는 함수
   */
  const fetchCourses = async () => {
    const res = await fetch('/api/courses');
    let data: any = [];
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    setCourses(Array.isArray(data) ? data : []);
  };

  /**
   * 장바구니 목록을 서버에서 가져오는 함수
   */
  const fetchCart = async () => {
    const res = await fetch('/api/cart');
    let data: any = [];
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    setCart(Array.isArray(data) ? data : []);
  };

  /**
   * 강의를 장바구니에 추가하는 함수
   * @param {string} courseId - 추가할 강의 ID
   */
  const addToCart = async (courseId: string) => {
    const res = await fetch('/api/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ courseId })
    });
    let data: any = {};
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    fetchCart();
  };

  /**
   * 장바구니에서 강의를 제거하는 함수
   * @param {string} courseId - 제거할 강의 ID
   */
  const removeFromCart = async (courseId: string) => {
    const res = await fetch(`/api/cart/${courseId}`, { method: 'DELETE' });
    let data: any = {};
    try { data = await res.json(); } catch { }
    if (openCaptchaIfNeeded(data)) return;
    fetchCart();
  };

  /**
   * 수강신청을 실행하는 함수
   * 장바구니에 담긴 모든 강의에 대해 신청을 진행합니다.
   */
  const enroll = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch('/api/enroll', { method: 'POST' });
      let data: any = null;
      try { data = await res.json(); } catch { }
      if (openCaptchaIfNeeded(data)) return;
      const okCount = (data?.results || []).filter((r: any) => r.success).length;
      const failCount = (data?.results || []).length - okCount;
      setMessage(`신청 완료: 성공 ${okCount}건, 실패 ${failCount}건`);
      await fetchCourses();
      await fetchCart();
    } finally {
      setLoading(false);
    }
  };

  /**
   * 캡차 인증을 제출하는 함수
   * 캡차 인증 성공 시 수강신청을 재시도합니다.
   */
  const submitCaptcha = async () => {
    if (!captchaModal.captchaId) return;
    setCaptchaMsg('');
    const res = await fetch('/api/enroll/unlock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ captchaId: captchaModal.captchaId, userInput: captchaInput })
    });
    const data = await res.json();
    if (data?.success) {
      setCaptchaModal({ open: false });
      setCaptchaInput('');
      setUiCaptchaRequired(false);
      clickTimesRef.current = [];
      // 캡차 인증 성공 후 수강신청 재시도
      await enroll();
    } else {
      setCaptchaMsg(data?.message || 'CAPTCHA 인증 실패');
    }
  };

  /**
   * 새로운 캡차를 생성하고 모달을 여는 함수
   */
  const refreshCaptcha = async () => {
    setCaptchaMsg('');
    setCaptchaInput('');
    const res = await fetch('/api/captcha/generate');
    const data = await res.json();
    setCaptchaModal({ open: true, captchaId: data?.captchaId, audioPath: data?.audioPath });
  };

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchCourses();
    fetchCart();
  }, []);

  // 장바구니에 담긴 강의 ID들을 Set으로 변환 (성능 최적화)
  const cartIdSet = useMemo(() => new Set(cart.map((c) => c.courseId)), [cart]);

  return (
    <div className={styles.coursesPage}>
      {/* Header */}
      <header className={styles.coursesHeader}>
        <div className={styles.headerTitleSection}>
          <h1 className={styles.headerTitle}>수강신청</h1>
          <span className={styles.headerSubtitle}>데모</span>
        </div>
        <div className={styles.headerActions}>
          <span className={styles.cartCount}>장바구니 {cart.length}개</span>
          <button
            onClick={handleLogout}
            className={`${styles.buttonBase} ${styles.logoutButton}`}
          >
            로그아웃
          </button>
          <button
            onClick={enroll}
            disabled={loading || cart.length === 0}
            className={`${styles.buttonBase} ${styles.enrollButton} ${(loading || cart.length === 0) ? styles.enrollButtonDisabled : ''}`}
          >
            {loading ? '신청 중…' : '수강신청'}
          </button>
        </div>
      </header>

      {/* Content */}
      <div className={styles.coursesContent}>
        <section>
          <div className={styles.coursesListHeader}>
            <div>
              <div className={styles.coursesListTitle}>개설 강의 목록</div>
              <div className={styles.coursesListSubtitle}>정원/시간표 확인 후 장바구니에 담아 신청하세요.</div>
            </div>
          </div>

          <div className={styles.coursesGrid}>
            {courses.map((c) => (
              <div key={c.courseId} className={styles.courseCard}>
                <div className={styles.courseCardContent}>
                  <div className={styles.courseCardHeader}>
                    <strong className={styles.courseTitle}>{c.title}</strong>
                    <span className={styles.courseId}>{c.courseId}</span>
                  </div>
                  <div className={styles.courseProfessor}>{c.professor}</div>
                  <div className={styles.courseSchedule}>{c.schedule}</div>
                </div>
                <div className={styles.courseCardFooter}>
                  <div className={styles.courseCapacity}>정원 {c.enrolled}/{c.capacity}</div>
                  {(() => {
                    const inCart = cartIdSet.has(c.courseId);
                    const disabled = inCart || c.enrolled >= c.capacity;
                    return (
                      <button
                        onClick={() => addToCart(c.courseId)}
                        disabled={disabled}
                        className={`${styles.buttonBase} ${styles.addToCartButton} ${disabled ? styles.addToCartButtonDisabled : ''}`}
                      >
                        {inCart ? '담김' : '장바구니'}
                      </button>
                    );
                  })()}
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside className={styles.cartSidebar}>
          <div className={styles.cartContainer}>
            <h2 className={styles.cartTitle}>장바구니</h2>
            <div className={styles.cartContent}>
              {cart.length === 0 && <div className={styles.cartEmpty}>담긴 과목이 없습니다.</div>}
              {cart.map((c) => (
                <div key={c.courseId} className={styles.cartItem}>
                  <div>
                    <div className={styles.cartItemTitle}>{c.title}</div>
                    <div className={styles.cartItemId}>{c.courseId}</div>
                  </div>
                  <button
                    onClick={() => removeFromCart(c.courseId)}
                    className={`${styles.buttonBase} ${styles.removeButton}`}
                  >
                    제거
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={enroll}
              disabled={loading || cart.length === 0}
              className={`${styles.buttonBase} ${styles.enrollButton} ${styles.cartEnrollButton} ${(loading || cart.length === 0) ? styles.enrollButtonDisabled : ''}`}
            >
              {loading ? '신청 중…' : '수강신청'}
            </button>

            {message && <p className={styles.message}>{message}</p>}
          </div>
        </aside>
      </div>

      {/* Global fast-click detector */}
      <ClickDetector
        enabled
        onTrigger={async () => {
          setUiCaptchaRequired(true);
          await refreshCaptcha();
        }}
        clickTimesRef={clickTimesRef}
      />

      {/* CAPTCHA Modal */}
      {captchaModal.open && (
        <div className={styles.captchaModalOverlay}>
          <div className={styles.captchaModalContent}>
            <h3 className={styles.captchaModalTitle}>추가 인증이 필요합니다</h3>
            <p className={styles.captchaModalDescription}>아래 오디오를 듣고 들은 단어를 입력하세요.</p>
            <div className={styles.captchaAudioContainer}>
              <audio controls src={captchaModal.audioPath} className={styles.captchaAudio} />
            </div>
            <div className={styles.captchaInputSection}>
              <input
                value={captchaInput}
                onChange={(e) => setCaptchaInput(e.target.value)}
                placeholder="정답 입력"
                className={styles.captchaInput}
              />
              <button onClick={submitCaptcha} className={styles.captchaSubmitButton}>확인</button>
              <button onClick={refreshCaptcha} className={styles.captchaRefreshButton}>새로고침</button>
            </div>
            {captchaMsg && <p className={styles.captchaMessage}>{captchaMsg}</p>}
            <div className={styles.captchaModalActions}>
              <button onClick={() => setCaptchaModal({ open: false })} className={styles.captchaCloseButton}>닫기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 빠른 클릭을 감지하여 캡차를 트리거하는 컴포넌트
 * 3초 내에 5번 이상 클릭하면 캡차 인증을 요구합니다.
 * @param {ClickDetectorProps} props - 컴포넌트 props
 * @returns {null} 렌더링되지 않는 컴포넌트
 */
function ClickDetector({ enabled, onTrigger, clickTimesRef }: ClickDetectorProps) {
  useEffect(() => {
    if (!enabled) return;
    
    const handler = () => {
      const now = Date.now();
      const windowMs = 3000; // 3초 윈도우
      const threshold = 5; // 임계값: 5회 클릭
      
      // 3초 내의 클릭만 필터링
      const filtered = clickTimesRef.current.filter((t) => now - t < windowMs);
      filtered.push(now);
      clickTimesRef.current = filtered;
      
      // 임계값 도달 시 캡차 트리거
      if (filtered.length >= threshold) {
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


