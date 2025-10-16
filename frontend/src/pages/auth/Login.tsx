/**
 * 로그인 페이지 컴포넌트
 * 사용자 인증과 CAPTCHA 검증 기능을 제공합니다.
 * ID/PASSWORD 입력과 오디오 기반 CAPTCHA 인증을 통해 안전한 로그인을 보장합니다.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useLoginCaptcha } from './hooks/useLoginCaptcha';
import bgImage from '../../../images/Home_screen_background2.jpg';
import logoImage from '../../../images/logo.jpg';
import styles from './Login.module.css';

/**
 * LoginPage 컴포넌트 - 사용자 인증을 위한 로그인 페이지
 * CAPTCHA 검증과 함께 안전한 로그인 기능을 제공합니다.
 * @returns {JSX.Element} 로그인 페이지 JSX 요소
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();

  // 이미 로그인된 사용자는 수강신청 페이지로 리디렉션
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/courses', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // 로그인 폼 상태 관리
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginMsg, setLoginMsg] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);

  // CAPTCHA 상태 및 함수 (useLoginCaptcha 훅 사용)
  const {
    captcha,
    captchaInput,
    captchaMsg,
    captchaVerified,
    setCaptchaInput,
    fetchCaptcha,
    verifyCaptcha
  } = useLoginCaptcha();

  /**
   * 로그인을 처리하는 함수
   * CAPTCHA 검증이 완료된 경우에만 로그인을 시도합니다.
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

  return (
    <div
      className={styles.loginPage}
      style={{ backgroundImage: `url(${bgImage})` }}
    >
      <div className={styles.loginFormContainer}>
        {/* 로그인 페이지 헤더 - 로고와 타이틀 */}
        <div className={styles.loginHeader}>
          <img src={logoImage} alt="logo" className={styles.loginLogo} />
          <h1 className={styles.loginTitle}>로그인</h1>
        </div>

        <div className={styles.loginForm}>
          {/* 사용자 ID 입력 필드 */}
          <label className={styles.formLabel}>ID</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder=""
            className={styles.formInput}
          />

          {/* 사용자 비밀번호 입력 필드 */}
          <label className={styles.formLabelPassword}>PASSWORD</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder=""
            className={styles.formInput}
          />

          {/* 오디오 캡차 섹션 */}
          <div className={styles.captchaSection}>
            <div className={styles.captchaHeader}>
              <strong>AUDIO CAPTCHA</strong>
              {/* 캡차 새로고침 버튼 */}
              <button onClick={fetchCaptcha} className={styles.captchaRefreshBtn}>REFRESH</button>
            </div>
            {captcha && (
              <div className={styles.captchaContent}>
                {/* 오디오 캡차 플레이어 */}
                <audio controls src={captcha.audioPath} className={styles.captchaAudioElement} />
                <div className={styles.captchaInputRow}>
                  {/* 캡차 답안 입력 필드 */}
                  <input
                    value={captchaInput}
                    onChange={(e) => setCaptchaInput(e.target.value)}
                    placeholder="ENTER ANSWER"
                    className={styles.captchaInputField}
                  />
                  {/* 캡차 검증 버튼 */}
                  <button onClick={verifyCaptcha} className={styles.captchaVerifyBtn}>VERIFY</button>
                </div>
                {/* 캡차 검증 결과 메시지 */}
                {captchaMsg && <p className={styles.captchaMessage}>{captchaMsg}</p>}
              </div>
            )}
          </div>

          {/* 로그인 실행 버튼 - 모든 조건이 만족되어야 활성화 */}
          <button
            onClick={onLogin}
            disabled={loggingIn || !captchaVerified || !username || !password}
            className={styles.loginButton}
          >
            {loggingIn ? '로그인 중…' : '로그인'}
          </button>
          {/* 로그인 결과 메시지 */}
          {loginMsg && <p className={styles.loginMessage}>{loginMsg}</p>}
        </div>
      </div>
    </div>
  );
}