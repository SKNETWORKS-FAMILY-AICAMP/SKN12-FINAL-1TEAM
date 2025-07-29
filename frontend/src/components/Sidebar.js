import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import SettingsModal from './SettingsModal';
import './Sidebar.css';

const Sidebar = ({ sidebarVisible, setSidebarVisible }) => {
  const location = useLocation();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const menuItems = [
    { path: '/', icon: '🏠', label: '홈' },
    { path: '/search', icon: '🔍', label: '검색' },
    { path: '/chat', icon: '💬', label: '채팅' },
    { path: '/docs', icon: '📄', label: '문서 생성' },
    { path: '/client', icon: '👥', label: '고객 관리' },
    { path: '/employee', icon: '👤', label: '실적 확인' },
    { path: '/schedule', icon: '📅', label: '일정 관리' },
  ];

  const handleSettingsClick = () => {
    setIsSettingsOpen(true);
  };

  const handleCloseSettings = () => {
    setIsSettingsOpen(false);
  };

  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  return (
    <>
      {/* Header */}
      <header className="main-header">
        <div className="header-left">
          <button 
            className="sidebar-toggle-btn"
            onClick={toggleSidebar}
            title={sidebarVisible ? "사이드바 숨기기" : "사이드바 보이기"}
          >
            ☰
          </button>
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Pharma-Helper</span>
          </div>
        </div>
        
        <div className="header-right">
          <div className="header-actions">
            <button className="notification-btn" title="알림">
              🔔
            </button>
            <div className="user-profile">
              <img 
                src="https://via.placeholder.com/32x32.png?text=👤" 
                alt="사용자" 
                title="프로필"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <div className={`sidebar ${sidebarVisible ? 'visible' : 'hidden'}`}>
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>
        
        <div className="sidebar-footer">
          <div className="nav-item settings-item" onClick={handleSettingsClick}>
            <span className="nav-icon">⚙️</span>
            <span className="nav-label">설정</span>
          </div>
          <div className="server-info">
            localhost:3000
          </div>
        </div>
      </div>

      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={handleCloseSettings} 
      />
    </>
  );
};

export default Sidebar; 