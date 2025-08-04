import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { verifyToken, logoutUser } from './services/api';
import './App.css';

// Components
import Sidebar from './components/Sidebar';
import Main from './components/Main';
import SearchPage from './components/Search';
import ChatBot from './components/ChatBot';
import Docs from './components/Docs';
import ClientAnalysis from './components/ClientAnalysis';
import Employee from './components/Employee';
import Schedule from './components/Schedule';
import Login from './components/Login';
import Admin from './components/Admin';

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
          // 토큰 유효성 검증
          await verifyToken();
          
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
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
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
            <Route path="/" element={<Main currentUser={currentUser} />} />
            <Route path="/search" element={<SearchPage currentUser={currentUser} />} />
            <Route path="/chat" element={<ChatBot currentUser={currentUser} />} />
            <Route path="/docs" element={<Docs currentUser={currentUser} />} />
            <Route path="/client" element={<ClientAnalysis currentUser={currentUser} />} />
            <Route path="/employee-performance" element={<Employee currentUser={currentUser} />} />
            <Route path="/schedule" element={<Schedule currentUser={currentUser} />} />
            <Route path="/admin" element={<Admin currentUser={currentUser} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
