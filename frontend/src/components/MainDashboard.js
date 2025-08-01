import React from 'react';
import { useNavigate } from 'react-router-dom';
import './MainDashboard.css';

function MainDashboard() {
  const navigate = useNavigate();
  return (
    <div className="main-dashboard">
      <div className="sidebar">
        <div className="logo">
          <h2>Pharma-Helper</h2>
        </div>
        <nav className="nav-menu">
          <ul>
            <li className="nav-item active">
              <span className="nav-icon">🏠</span>
              <span className="nav-text">홈</span>
            </li>
            <li className="nav-item">
              <span className="nav-icon">📅</span>
              <span className="nav-text">일정 관리</span>
            </li>
            <li className="nav-item">
              <span className="nav-icon">📊</span>
              <span className="nav-text">보고서</span>
            </li>
            <li className="nav-item">
              <span className="nav-icon">👥</span>
              <span className="nav-text">고객 관리</span>
            </li>
            <li className="nav-item">
              <span className="nav-icon">🤖</span>
              <span className="nav-text">AI 코칭</span>
            </li>
            <li className="nav-item" onClick={() => navigate('/chat')}>
              <span className="nav-icon">💬</span>
              <span className="nav-text">채팅</span>
            </li>
            <li className="nav-item" onClick={() => navigate('/performance')}>
              <span className="nav-icon">👤</span>
              <span className="nav-text">본인 실적 확인</span>
            </li>
          </ul>
        </nav>
        <div className="sidebar-bottom">
          <div className="nav-item">
            <span className="nav-icon">⚙️</span>
            <span className="nav-text">설정</span>
          </div>
        </div>
      </div>
      <div className="main-content">
        <div className="welcome-section">
          <h1>김복남님, 좋은 하루입니다!</h1>
        </div>
        <div className="dashboard-cards">
          <div className="card">
            <h3>오늘 방문 일정</h3>
            <p className="card-value">3건</p>
          </div>
          <div className="card">
            <h3>미제출 보고서</h3>
            <p className="card-value">1건</p>
          </div>
          <div className="card">
            <h3>이번 주 실적 달성률</h3>
            <p className="card-value">85%</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MainDashboard; 