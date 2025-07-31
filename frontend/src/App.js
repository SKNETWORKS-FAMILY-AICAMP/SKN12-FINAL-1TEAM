<<<<<<< HEAD
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { verifyToken, logoutUser } from './services/api';
import './App.css';

// Components
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import SearchPage from './components/SearchPage';
import ChatScreen from './components/ChatScreen';
import DocsPage from './components/DocsPage';
import ClientPage from './components/ClientPage';
import EmployeePerformance from './components/EmployeePerformance';
import SchedulePage from './components/SchedulePage';
import LoginPage from './components/LoginPage';
import AdminPage from './components/AdminPage';

function App() {
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // 컴포넌트 마운트 시 로그인 상태 확인
  useEffect(() => {
    const checkLoginStatus = async () => {
      const token = localStorage.getItem('narutalk_token');
      const userData = localStorage.getItem('narutalk_user');
      
      if (token && userData) {
        try {
          // 토큰 유효성 검증 (선택사항 - 백엔드에 /user/me 엔드포인트가 있는 경우)
          // await verifyToken();
          
          setIsLoggedIn(true);
          setCurrentUser(JSON.parse(userData));
        } catch (error) {
          // 토큰이 유효하지 않은 경우 로그아웃 처리
          console.error('Token verification failed:', error);
          logoutUser();
          setIsLoggedIn(false);
          setCurrentUser(null);
        }
      }
      
      setIsLoading(false);
    };

    checkLoginStatus();
  }, []);

  const handleLogin = (userData) => {
    setIsLoggedIn(true);
    setCurrentUser(userData);
  };

  const handleLogout = () => {
    logoutUser();
    setIsLoggedIn(false);
    setCurrentUser(null);
  };

  // 로딩 중일 때 표시할 컴포넌트
  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-spinner-large"></div>
          <p>Narutalk 로딩 중...</p>
        </div>
      </div>
    );
  }

  // 로그인되지 않은 경우 로그인 페이지 표시
  if (!isLoggedIn) {
    return (
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    );
  }

  // 로그인된 경우 메인 애플리케이션 표시
  return (
    <Router>
      <div className="App">
        <Sidebar 
          sidebarVisible={sidebarVisible} 
          setSidebarVisible={setSidebarVisible}
          currentUser={currentUser}
          onLogout={handleLogout}
        />
        <div className={`main-content ${!sidebarVisible ? 'sidebar-hidden' : ''}`}>
          <Routes>
            <Route path="/" element={<Dashboard currentUser={currentUser} />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chat" element={<ChatScreen />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/client" element={<ClientPage />} />
            <Route path="/employee" element={<EmployeePerformance currentUser={currentUser} />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/admin" element={<AdminPage currentUser={currentUser} />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
=======
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import MainDashboard from './components/MainDashboard';
import ChatScreen from './components/ChatScreen';
import EmployeePerformance from './components/EmployeePerformance';

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/" element={<MainDashboard />} />
          <Route path="/chat" element={<ChatScreen />} />
          <Route path="/performance" element={<EmployeePerformance />} />
        </Routes>
      </Router>
    </div>
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
  );
}

export default App;
