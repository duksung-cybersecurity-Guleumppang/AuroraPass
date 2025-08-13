import React, { useEffect, useMemo, useState } from 'react';
import bgImage from '../../images/Home_screen_background.jpg';
import logoImage from '../../images/logo.jpg';

type Captcha = { captchaId: string; audioPath: string };

export default function LoginPage() {
  const defaultUsername = useMemo(() => import.meta.env.VITE_LOGIN_USERNAME || '', []);
  const defaultPassword = useMemo(() => import.meta.env.VITE_LOGIN_PASSWORD || '', []);

  const [username, setUsername] = useState(defaultUsername);
  const [password, setPassword] = useState(defaultPassword);
  const [captcha, setCaptcha] = useState<Captcha | null>(null);
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaMsg, setCaptchaMsg] = useState('');
  const [captchaVerified, setCaptchaVerified] = useState(false);
  const [loginMsg, setLoginMsg] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);

  const fetchCaptcha = async () => {
    setCaptchaMsg('');
    setCaptchaVerified(false);
    setCaptchaInput('');
    const res = await fetch('/api/captcha/generate');
    const data = await res.json();
    setCaptcha(data);
  };

  const verifyCaptcha = async () => {
    if (!captcha) return;
    const res = await fetch('/api/captcha/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ captchaId: captcha.captchaId, userInput: captchaInput })
    });
    const data = await res.json();
    setCaptchaMsg(data.message || (data.success ? '성공' : '실패'));
    setCaptchaVerified(!!data.success);
  };

  const onLogin = async () => {
    if (!captchaVerified) return;
    setLoggingIn(true);
    setLoginMsg('');
    try {
      const res = await fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      setLoginMsg(data?.message ?? '');
    } catch (e) {
      setLoginMsg('로그인 요청 중 오류가 발생했습니다.');
    } finally {
      setLoggingIn(false);
    }
  };

  useEffect(() => { fetchCaptcha(); }, []);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundImage: `url(${bgImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24
    }}>
      <div style={{
        width: 420,
        background: 'rgba(255,255,255,0.9)',
        borderRadius: 12,
        boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
        padding: 24,
        backdropFilter: 'blur(4px)'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 16 }}>
          <img src={logoImage} alt="logo" style={{ width: 120, height: 'auto', borderRadius: 8 }} />
          <h1 style={{ margin: '12px 0 0', fontSize: 20 }}>로그인</h1>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <label style={{ fontSize: 14 }}>아이디</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="아이디"
            style={{ padding: '10px 12px', border: '1px solid #ddd', borderRadius: 8 }}
          />

          <label style={{ fontSize: 14, marginTop: 6 }}>비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호"
            style={{ padding: '10px 12px', border: '1px solid #ddd', borderRadius: 8 }}
          />

          <div style={{ marginTop: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <strong>오디오 CAPTCHA</strong>
              <button onClick={fetchCaptcha} style={{ padding: '6px 10px' }}>새로고침</button>
            </div>
            {captcha && (
              <div style={{ marginTop: 8 }}>
                <audio controls src={captcha.audioPath} style={{ width: '100%' }} />
                <div style={{ marginTop: 6, display: 'flex', gap: 8 }}>
                  <input
                    value={captchaInput}
                    onChange={(e) => setCaptchaInput(e.target.value)}
                    placeholder="정답 입력"
                    style={{ flex: 1, padding: '8px 10px', border: '1px solid #ddd', borderRadius: 8 }}
                  />
                  <button onClick={verifyCaptcha} style={{ padding: '8px 12px' }}>검증</button>
                </div>
                {captchaMsg && <p style={{ marginTop: 6, fontSize: 13 }}>{captchaMsg}</p>}
              </div>
            )}
          </div>

          <button
            onClick={onLogin}
            disabled={loggingIn || !captchaVerified || !username || !password}
            style={{
              marginTop: 14,
              padding: '12px 14px',
              borderRadius: 10,
              border: 'none',
              color: 'white',
              background: (loggingIn || !captchaVerified || !username || !password) ? '#b5c0c9' : '#2563eb',
              cursor: (loggingIn || !captchaVerified || !username || !password) ? 'not-allowed' : 'pointer',
              fontWeight: 600
            }}
          >
            {loggingIn ? '로그인 중…' : '로그인'}
          </button>
          {loginMsg && <p style={{ marginTop: 8, fontSize: 13 }}>{loginMsg}</p>}
        </div>
      </div>
    </div>
  );
}


