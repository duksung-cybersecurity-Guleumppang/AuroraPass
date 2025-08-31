/**
 * 로그인 페이지 컴포넌트
 * 사용자 인증과 캡차 검증 기능을 제공합니다.
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Captcha } from './Login.types';
import bgImage from '../../images/Home_screen_background.jpg';
import logoImage from '../../images/logo.jpg';
import styles from './Login.module.css';

/**
 * 로그인 메인 페이지 컴포넌트
 * @returns {JSX.Element} 로그인 페이지 JSX
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  
  // 플레이스홀더 값 (환경변수에서 가져올 수 있지만 현재는 빈 값)
  const placeholderUsername = useMemo(() => '', []);
  const placeholderPassword = useMemo(() => '', []);

  // 이미 로그인된 사용자는 수강신청 페이지로 리디렉션
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/courses', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // 상태 관리
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [captcha, setCaptcha] = useState<Captcha | null>(null);
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaMsg, setCaptchaMsg] = useState('');
  const [captchaVerified, setCaptchaVerified] = useState(false);
  const [loginMsg, setLoginMsg] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);

  /**
   * 새로운 캡차를 서버에서 가져오는 함수
   * 캡차 상태를 초기화하고 새로운 캡차 데이터를 받아옵니다.
   */
  const fetchCaptcha = async () => {
    setCaptchaMsg('');
    setCaptchaVerified(false);
    setCaptchaInput('');
    const res = await fetch('/api/captcha/generate');
    const data = await res.json();
    setCaptcha(data);
  };

  /**
   * 캡차 인증을 확인하는 함수
   * 사용자가 입력한 캡차 답안을 서버에서 검증합니다.
   */
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

  /**
   * 로그인을 처리하는 함수
   * 캡차 검증이 완료된 경우에만 로그인을 시도합니다.
   */
  const onLogin = async () => {
    if (!captchaVerified) return;
    setLoggingIn(true);
    setLoginMsg('');
    try {
      const success = await login(username, password);
      if (success) {
        navigate('/courses');
      } else {
        setLoginMsg('로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.');
      }
    } catch (e) {
      setLoginMsg('로그인 요청 중 오류가 발생했습니다.');
    } finally {
      setLoggingIn(false);
    }
  };

  // 컴포넌트 마운트 시 캡차 생성
  useEffect(() => { fetchCaptcha(); }, []);

  return (
    <div className={styles.loginPage} style={{ backgroundImage: `url(${bgImage})` }}>
      <div className={styles.loginFormContainer}>
        <div className={styles.loginHeader}>
          <img src={logoImage} alt="logo" className={styles.loginLogo} />
          <h1 className={styles.loginTitle}>로그인</h1>
        </div>

        <div className={styles.loginForm}>
          <label className={styles.formLabel}>아이디</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder={placeholderUsername}
            className={styles.formInput}
          />

          <label className={styles.formLabelPassword}>비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={placeholderPassword}
            className={styles.formInput}
          />

          <div className={styles.captchaSection}>
            <div className={styles.captchaHeader}>
              <strong>오디오 CAPTCHA</strong>
              <button onClick={fetchCaptcha} className={styles.captchaRefreshBtn}>새로고침</button>
            </div>
            {captcha && (
              <div className={styles.captchaContent}>
                <audio controls src={captcha.audioPath} className={styles.captchaAudioElement} />
                <div className={styles.captchaInputRow}>
                  <input
                    value={captchaInput}
                    onChange={(e) => setCaptchaInput(e.target.value)}
                    placeholder="정답 입력"
                    className={styles.captchaInputField}
                  />
                  <button onClick={verifyCaptcha} className={styles.captchaVerifyBtn}>검증</button>
                </div>
                {captchaMsg && <p className={styles.captchaMessage}>{captchaMsg}</p>}
              </div>
            )}
          </div>

          <button
            onClick={onLogin}
            disabled={loggingIn || !captchaVerified || !username || !password}
            className={styles.loginButton}
          >
            {loggingIn ? '로그인 중…' : '로그인'}
          </button>
          {loginMsg && <p className={styles.loginMessage}>{loginMsg}</p>}
        </div>
      </div>
    </div>
  );
}


