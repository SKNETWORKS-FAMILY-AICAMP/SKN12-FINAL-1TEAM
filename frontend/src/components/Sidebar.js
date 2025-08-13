import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Setting from './Setting';
import Notification from './Notification';
import UserModal from './UserModal';
import './Sidebar.css';

const Sidebar = ({ sidebarVisible, setSidebarVisible, currentUser, onLogout }) => {
  const location = useLocation();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  
  const isAdmin = currentUser?.role === 'admin';

  // 관리자용 알림 데이터
  const adminNotifications = [
    {
      type: 'info',
      title: '시스템 업데이트',
      message: '새로운 보안 패치가 적용되었습니다.',
      time: '10분 전'
    },
    {
      type: 'warning',
      title: '디스크 용량 부족',
      message: '서버 디스크 용량이 80%를 초과했습니다.',
      time: '1시간 전'
    }
  ];

  // 일반 사용자용 알림 데이터
  const userNotifications = [
    {
      type: 'info',
      title: '새로운 방문 일정',
      message: '내일 오후 2시 ABC병원 방문 예정입니다.',
      time: '5분 전'
    },
  ];

  const notifications = isAdmin ? adminNotifications : userNotifications;

  // 관리자용 메뉴
  const adminMenuItems = [
    { path: '/', icon: '🏠', label: '관리자 홈' },
    { path: '/search', icon: '🔍', label: '검색' },
    { path: '/chat', icon: '💬', label: '채팅' },
    { path: '/docs', icon: '📄', label: '문서 생성' },
    { path: '/client', icon: '👥', label: '고객 관리' },
    { path: '/employee', icon: '📊', label: '직원 실적 분석' },
    { path: '/admin', icon: '⚙️', label: '시스템 관리' },
  ];

  // 일반 사용자용 메뉴
  const userMenuItems = [
    { path: '/', icon: '🏠', label: '홈' },
    { path: '/search', icon: '🔍', label: '검색' },
    { path: '/chat', icon: '💬', label: '채팅' },
    { path: '/docs', icon: '📄', label: '문서 생성' },
    { path: '/client', icon: '👥', label: '고객 관리' },
    { path: '/employee', icon: '👤', label: '실적 확인' },
    { path: '/schedule', icon: '📅', label: '일정 관리' },
  ];

  const menuItems = isAdmin ? adminMenuItems : userMenuItems;

  const handleSettingsClick = () => {
    setIsSettingsOpen(true);
  };

  const handleCloseSettings = () => {
    setIsSettingsOpen(false);
  };

  const handleNotificationClick = () => {
    setIsNotificationModalOpen(true);
  };

  const handleUserClick = () => {
    setIsUserModalOpen(true);
  };

  const handleLogout = () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      onLogout();
    }
  };

  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  // 사용자 아바타에 표시할 이니셜 (이름의 첫 글자)
  const userInitial = currentUser?.name ? currentUser.name.charAt(0) : '관';

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
            <span className="logo-text">Narutalk</span>
            {isAdmin && (
              <span className="admin-indicator" style={{
                backgroundColor: '#dc3545',
                color: 'white',
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '10px',
                marginLeft: '8px',
                fontWeight: 'bold'
              }}>
                ADMIN
              </span>
            )}
          </div>
        </div>
        
        <div className="header-right">
          <div className="header-actions">
            <button 
              className="notification-btn" 
              title="알림" 
              onClick={handleNotificationClick}
              style={{ position: 'relative' }}
            >
              🔔
              {notifications.length > 0 && (
                <span className="notification-badge" style={{
                  position: 'absolute',
                  top: '-8px',
                  right: '-8px',
                  backgroundColor: '#dc3545',
                  color: 'white',
                  borderRadius: '50%',
                  width: '20px',
                  height: '20px',
                  fontSize: '11px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  border: '2px solid white',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                }}>
                  {notifications.length}
                </span>
              )}
            </button>
            <div className="user-profile" onClick={handleUserClick}>
              <div className="user-avatar" data-initial={userInitial} style={{
                backgroundColor: isAdmin ? '#dc3545' : '#007bff'
              }}></div>
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
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              fontSize: '12px'
            }}>
              {isAdmin && (
                <span style={{
                  backgroundColor: '#dc3545',
                  color: 'white',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  fontSize: '10px',
                  fontWeight: 'bold'
                }}>
                  🛡️ ADMIN
                </span>
              )}
              <div>
                <div style={{ fontWeight: 'bold' }}>
                  {currentUser?.name || '사용자'}
                </div>
                <div style={{ opacity: 0.7 }}>
                  {currentUser?.department || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Setting 
        isOpen={isSettingsOpen} 
        onClose={handleCloseSettings}
        onLogout={onLogout}
        currentUser={currentUser}
      />
      
      <Notification 
        isOpen={isNotificationModalOpen}
        onClose={() => setIsNotificationModalOpen(false)}
        notifications={notifications}
      />
      
      <UserModal
        isOpen={isUserModalOpen}
        onClose={() => setIsUserModalOpen(false)}
        userData={currentUser}
      />
    </>
  );
};

export default Sidebar; 