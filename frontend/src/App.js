import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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

function App() {
  const [sidebarVisible, setSidebarVisible] = useState(true);

  return (
    <Router>
      <div className="App">
        <Sidebar sidebarVisible={sidebarVisible} setSidebarVisible={setSidebarVisible} />
        <div className={`main-content ${!sidebarVisible ? 'sidebar-hidden' : ''}`}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chat" element={<ChatScreen />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/client" element={<ClientPage />} />
            <Route path="/employee" element={<EmployeePerformance />} />
            <Route path="/schedule" element={<SchedulePage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
