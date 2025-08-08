import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser, verifyToken } from '../services/api';
import './LoginPage.css';

const LoginPage = ({ onLogin }) => {
  const navigate = useNavigate();
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({
      ...prev,
      [name]: value
    }));
    // 입력 시 에러 메시지 초기화
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!loginData.email || !loginData.password) {
      setError('이메일과 비밀번호를 입력해주세요.');
      return;
    }

    // 이메일 형식 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(loginData.email)) {
      setError('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await loginUser({
        username: loginData.email,
        password: loginData.password
      });

      // 로그인 성공 - 토큰 저장
      const { access_token, token_type } = response;
      localStorage.setItem('narutalk_token', access_token);
      localStorage.setItem('narutalk_token_type', token_type);

      // 토큰으로 실제 사용자 정보 가져오기
      const userInfo = await verifyToken();

      // 백엔드에서 받은 사용자 정보 사용
      const userData = {
        email: userInfo.email,
        name: userInfo.name,
        role: userInfo.role,
        username: userInfo.username,
        company: '좋은제약',
        department: userInfo.role === 'admin' ? '시스템 관리부' : '영업부',
        position: userInfo.role === 'admin' ? '시스템 관리자' : '영업사원',
        phone: '010-1234-5678'
      };

      // 로컬 스토리지에 사용자 정보 저장
      localStorage.setItem('narutalk_user', JSON.stringify(userData));
      localStorage.setItem('narutalk_isLoggedIn', 'true');

      // 부모 컴포넌트에 로그인 상태 전달
      if (onLogin) {
        onLogin(userData);
      }

      // 대시보드로 이동
      navigate('/');

    } catch (error) {
      setError(error.message || '로그인에 실패했습니다. 사용자명과 비밀번호를 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  };



  return (
    <div className="login-page">
      <div className="login-background">
        <div className="background-pattern"></div>
      </div>
      
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="company-logo">
              <span className="logo-icon">💊</span>
              <h1 className="company-name">좋은제약</h1>
            </div>
            <h2 className="app-name">Narutalk</h2>
            <p className="app-description">제약영업사원을 위한 AI 업무 파트너</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">이메일</label>
              <input
                type="email"
                id="email"
                name="email"
                value={loginData.email}
                onChange={handleInputChange}
                placeholder="이메일을 입력하세요"
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">비밀번호</label>
              <input
                type="password"
                id="password"
                name="password"
                value={loginData.password}
                onChange={handleInputChange}
                placeholder="비밀번호를 입력하세요"
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <button 
              type="submit" 
              className={`login-button ${isLoading ? 'loading' : ''}`}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="loading-spinner"></span>
                  로그인 중...
                </>
              ) : (
                '로그인'
              )}
            </button>

          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 