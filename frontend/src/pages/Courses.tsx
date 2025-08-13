import React, { useEffect, useMemo, useRef, useState } from 'react';

type Course = {
  courseId: string;
  title: string;
  professor: string;
  schedule: string;
  capacity: number;
  enrolled: number;
};

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [cart, setCart] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [captchaModal, setCaptchaModal] = useState<{ open: boolean; captchaId?: string; audioPath?: string }>({ open: false });
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaMsg, setCaptchaMsg] = useState('');
  const [uiCaptchaRequired, setUiCaptchaRequired] = useState(false);
  const clickTimesRef = useRef<number[]>([]);

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

  const fetchCourses = async () => {
    const res = await fetch('/api/courses');
    let data: any = [];
    try { data = await res.json(); } catch {}
    if (openCaptchaIfNeeded(data)) return;
    setCourses(Array.isArray(data) ? data : []);
  };

  const fetchCart = async () => {
    const res = await fetch('/api/cart');
    let data: any = [];
    try { data = await res.json(); } catch {}
    if (openCaptchaIfNeeded(data)) return;
    setCart(Array.isArray(data) ? data : []);
  };

  const addToCart = async (courseId: string) => {
    const res = await fetch('/api/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ courseId })
    });
    let data: any = {};
    try { data = await res.json(); } catch {}
    if (openCaptchaIfNeeded(data)) return;
    fetchCart();
  };

  const removeFromCart = async (courseId: string) => {
    const res = await fetch(`/api/cart/${courseId}`, { method: 'DELETE' });
    let data: any = {};
    try { data = await res.json(); } catch {}
    if (openCaptchaIfNeeded(data)) return;
    fetchCart();
  };

  const enroll = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch('/api/enroll', { method: 'POST' });
      let data: any = null;
      try { data = await res.json(); } catch {}
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
      // 1회 허용으로 즉시 재시도
      await enroll();
    } else {
      setCaptchaMsg(data?.message || 'CAPTCHA 인증 실패');
    }
  };

  const refreshCaptcha = async () => {
    setCaptchaMsg('');
    setCaptchaInput('');
    const res = await fetch('/api/captcha/generate');
    const data = await res.json();
    setCaptchaModal({ open: true, captchaId: data?.captchaId, audioPath: data?.audioPath });
  };

  useEffect(() => {
    fetchCourses();
    fetchCart();
  }, []);

  const cartIdSet = useMemo(() => new Set(cart.map((c) => c.courseId)), [cart]);

  const colors = {
    bg: '#f6f8fb',
    surface: '#ffffff',
    text: '#0f172a',
    subText: '#64748b',
    border: '#e2e8f0',
    primary: '#2563eb',
    primaryHover: '#1d4ed8',
    danger: '#ef4444',
    dangerHover: '#dc2626'
  } as const;

  const buttonBase: React.CSSProperties = {
    padding: '10px 14px',
    borderRadius: 10,
    border: '1px solid transparent',
    fontWeight: 600,
    cursor: 'pointer'
  };

  return (
    <div style={{ minHeight: '100vh', background: colors.bg }}>
      {/* Header */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 10,
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        padding: '14px 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
          <h1 style={{ margin: 0, fontSize: 20, color: colors.text }}>수강신청</h1>
          <span style={{ color: colors.subText, fontSize: 13 }}>데모</span>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ color: colors.subText, fontSize: 14 }}>장바구니 {cart.length}개</span>
          <button
            onClick={enroll}
            disabled={loading || cart.length === 0}
            style={{
              ...buttonBase,
              background: (loading || cart.length === 0) ? '#cbd5e1' : colors.primary,
              color: '#fff',
              cursor: (loading || cart.length === 0) ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '신청 중…' : '수강신청'}
          </button>
        </div>
      </header>

      {/* Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24, padding: 24, maxWidth: 1200, margin: '0 auto' }}>
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: 16, color: colors.text, fontWeight: 700 }}>개설 강의 목록</div>
              <div style={{ fontSize: 13, color: colors.subText }}>정원/시간표 확인 후 장바구니에 담아 신청하세요.</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginTop: 16 }}>
            {courses.map((c) => (
              <div key={c.courseId} style={{
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: 12,
                boxShadow: '0 4px 12px rgba(15, 23, 42, 0.04)'
              }}>
                <div style={{ padding: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <strong style={{ color: colors.text }}>{c.title}</strong>
                    <span style={{ fontSize: 12, color: colors.subText }}>{c.courseId}</span>
                  </div>
                  <div style={{ marginTop: 6, fontSize: 14, color: colors.text }}>{c.professor}</div>
                  <div style={{ marginTop: 4, fontSize: 13, color: colors.subText }}>{c.schedule}</div>
                </div>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 14px', borderTop: `1px dashed ${colors.border}`
                }}>
                  <div style={{ fontSize: 13, color: colors.subText }}>정원 {c.enrolled}/{c.capacity}</div>
                  {(() => {
                    const inCart = cartIdSet.has(c.courseId);
                    const disabled = inCart || c.enrolled >= c.capacity;
                    return (
                      <button
                        onClick={() => addToCart(c.courseId)}
                        disabled={disabled}
                        style={{
                          ...buttonBase,
                          background: disabled ? '#cbd5e1' : colors.primary,
                          color: '#fff',
                          cursor: disabled ? 'not-allowed' : 'pointer'
                        }}
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

        <aside style={{ position: 'sticky', top: 76, alignSelf: 'start' }}>
          <div style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.04)',
            padding: 14
          }}>
            <h2 style={{ margin: 0, fontSize: 16, color: colors.text }}>장바구니</h2>
            <div style={{ marginTop: 8, minHeight: 180 }}>
              {cart.length === 0 && <div style={{ color: colors.subText, padding: '8px 4px' }}>담긴 과목이 없습니다.</div>}
              {cart.map((c) => (
                <div key={c.courseId} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 6px', borderBottom: `1px dashed ${colors.border}`
                }}>
                  <div>
                    <div style={{ fontWeight: 600, color: colors.text }}>{c.title}</div>
                    <div style={{ fontSize: 12, color: colors.subText }}>{c.courseId}</div>
                  </div>
                  <button
                    onClick={() => removeFromCart(c.courseId)}
                    style={{
                      ...buttonBase,
                      background: colors.danger,
                      color: '#fff'
                    }}
                  >
                    제거
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={enroll}
              disabled={loading || cart.length === 0}
              style={{
                ...buttonBase,
                width: '100%',
                marginTop: 8,
                background: (loading || cart.length === 0) ? '#cbd5e1' : colors.primary,
                color: '#fff',
                cursor: (loading || cart.length === 0) ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? '신청 중…' : '수강신청'}
            </button>

            {message && <p style={{ marginTop: 8, fontSize: 13, color: colors.text }}>{message}</p>}
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
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, width: 420 }}>
            <h3 style={{ marginTop: 0 }}>추가 인증이 필요합니다</h3>
            <p style={{ marginTop: 4, color: '#475569', fontSize: 14 }}>아래 오디오를 듣고 들은 단어를 입력하세요.</p>
            <div style={{ marginTop: 8 }}>
              <audio controls src={captchaModal.audioPath} style={{ width: '100%' }} />
            </div>
            <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
              <input
                value={captchaInput}
                onChange={(e) => setCaptchaInput(e.target.value)}
                placeholder="정답 입력"
                style={{ flex: 1, padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 8 }}
              />
              <button onClick={submitCaptcha} style={{ padding: '10px 14px', borderRadius: 8, background: '#2563eb', color: '#fff', fontWeight: 600 }}>확인</button>
              <button onClick={refreshCaptcha} style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #e2e8f0' }}>새로고침</button>
            </div>
            {captchaMsg && <p style={{ marginTop: 6, fontSize: 13, color: '#dc2626' }}>{captchaMsg}</p>}
            <div style={{ marginTop: 8, textAlign: 'right' }}>
              <button onClick={() => setCaptchaModal({ open: false })} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }}>닫기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ClickDetector({ enabled, onTrigger, clickTimesRef }: { enabled: boolean; onTrigger: () => void | Promise<void>; clickTimesRef: React.MutableRefObject<number[]> }) {
  useEffect(() => {
    if (!enabled) return;
    const handler = () => {
      const now = Date.now();
      const windowMs = 3000;
      const threshold = 5;
      const filtered = clickTimesRef.current.filter((t) => now - t < windowMs);
      filtered.push(now);
      clickTimesRef.current = filtered;
      if (filtered.length >= threshold) {
        clickTimesRef.current = [];
        onTrigger();
      }
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  }, [enabled, onTrigger, clickTimesRef]);
  return null;
}


