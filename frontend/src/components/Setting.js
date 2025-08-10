import React, { useState } from 'react';
import './Setting.css';

const Setting = ({ isOpen, onClose, onLogout, currentUser }) => {
  const [notifications, setNotifications] = useState(true);
  const [theme, setTheme] = useState('light');

  const handleLogout = () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      onLogout();
      onClose(); // 모달 닫기
    }
  };

  const handleNotificationToggle = () => {
    setNotifications(!notifications);
    alert(`알림이 ${!notifications ? '켜졌습니다.' : '꺼졌습니다.'}`);
  };

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    // 테마 변경 로직
    document.body.className = newTheme === 'dark' ? 'dark-theme' : '';
    alert(`${newTheme === 'dark' ? '다크' : '라이트'} 테마로 변경되었습니다.`);
  };

  if (!isOpen) return null;

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>⚙️ 설정</h2>
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-content">
          {/* 로그인/로그아웃 섹션 */}
          <div className="setting-section">
            <div className="setting-header">
              <h3>🔐 계정</h3>
            </div>
            <div className="setting-item">
              <div className="setting-info">
                <span className="setting-label">현재 사용자</span>
                <span className="setting-value">
                  {currentUser?.name || '사용자'} ({currentUser?.id || 'N/A'})
                </span>
              </div>
              <button 
                className="action-button logout"
                onClick={handleLogout}
              >
                로그아웃
              </button>
            </div>
          </div>

          {/* 알림 설정 섹션 */}
          <div className="setting-section">
            <div className="setting-header">
              <h3>🔔 알림</h3>
            </div>
            <div className="setting-item">
              <div className="setting-info">
                <span className="setting-label">알림 받기</span>
                <span className="setting-value">
                  {notifications ? '켜짐' : '꺼짐'}
                </span>
              </div>
              <button 
                className={`toggle-button ${notifications ? 'on' : 'off'}`}
                onClick={handleNotificationToggle}
              >
                <div className={`toggle-slider ${notifications ? 'on' : 'off'}`}></div>
              </button>
            </div>
          </div>

          {/* 테마 설정 섹션 */}
          <div className="setting-section">
            <div className="setting-header">
              <h3>🎨 테마</h3>
            </div>
            <div className="setting-item">
              <div className="setting-info">
                <span className="setting-label">테마 선택</span>
                <span className="setting-value">
                  {theme === 'light' ? '라이트' : '다크'}
                </span>
              </div>
              <div className="theme-buttons">
                <button 
                  className={`theme-button ${theme === 'light' ? 'active' : ''}`}
                  onClick={() => handleThemeChange('light')}
                >
                  ☀️ 라이트
                </button>
                <button 
                  className={`theme-button ${theme === 'dark' ? 'active' : ''}`}
                  onClick={() => handleThemeChange('dark')}
                >
                  🌙 다크
                </button>
              </div>
            </div>
          </div>


        </div>

        <div className="modal-footer">
          <button className="cancel-button" onClick={onClose}>
            취소
          </button>
          <button className="save-button">
            저장
          </button>
        </div>
      </div>
    </div>
  );
};

export default Setting; 