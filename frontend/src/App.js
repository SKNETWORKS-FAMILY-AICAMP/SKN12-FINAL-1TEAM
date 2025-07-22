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
  );
}

export default App;
