import React, { useState } from 'react';
import './EmployeePerformance.css';

function EmployeePerformance({ currentUser }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showDetailReport, setShowDetailReport] = useState(false);

  const isAdmin = currentUser?.role === 'admin';

  // 관리자용 직원 목록
  const employees = [
    { id: 'E001', name: '김민지', team: '영업 1팀', position: '영업사원', performance: 85, sales: 12500000 },
    { id: 'E002', name: '최수아', team: '영업 1팀', position: '영업사원', performance: 92, sales: 15800000 },
    { id: 'E003', name: '정다은', team: '영업 1팀', position: '영업사원', performance: 78, sales: 9800000 },
    { id: 'E004', name: '박준호', team: '영업 2팀', position: '팀장', performance: 88, sales: 14200000 },
    { id: 'E005', name: '이현우', team: '영업 2팀', position: '영업사원', performance: 95, sales: 16800000 },
    { id: 'E006', name: '강지훈', team: '영업 2팀', position: '영업사원', performance: 82, sales: 11200000 },
  ];

  // 검색 필터링된 직원 목록
  const filteredEmployees = employees.filter(employee =>
    employee.name.includes(searchQuery) || 
    employee.team.includes(searchQuery) ||
    employee.id.includes(searchQuery)
  );

  // 직원 클릭 핸들러
  const handleEmployeeClick = (employee) => {
    setSelectedEmployee(employee);
    setShowDetailReport(true);
  };

  // 뒤로가기 핸들러
  const handleBackToList = () => {
    setShowDetailReport(false);
    setSelectedEmployee(null);
  };

  // 관리자가 아닌 경우 개인 실적 페이지
  if (!isAdmin) {
    return (
      <div className="employee-performance">
        <div className="performance-header">
          <h1>내 실적 확인</h1>
        </div>

        <div className="performance-container">
          <div className="performance-sidebar">
            <div className="employee-info">
              <h3>내 정보</h3>
              <div className="employee-card">
                <div className="employee-avatar">
                  <img src="https://via.placeholder.com/60x60" alt="Employee" />
                </div>
                <div className="employee-details">
                  <h4>{currentUser?.name || '사용자'}</h4>
                  <p>{currentUser?.team || '영업 1팀'}</p>
                  <p>{currentUser?.position || '영업사원'}</p>
                </div>
              </div>
            </div>

            <div className="analysis-actions">
              <h3>분석 도구</h3>
              <button className="analyze-btn">
                실적 분석
              </button>
              <button className="generate-report-btn">
                보고서 생성
              </button>
            </div>
          </div>

          <div className="performance-main">
            <div className="performance-overview">
              <h2>내 실적 개요</h2>
              <div className="performance-stats">
                <div className="stat-card">
                  <h3>총 매출</h3>
                  <p className="stat-value">12,500,000원</p>
                </div>
                <div className="stat-card">
                  <h3>평균 실적</h3>
                  <p className="stat-value">85%</p>
                </div>
                <div className="stat-card">
                  <h3>목표 달성률</h3>
                  <p className="stat-value">92%</p>
                </div>
              </div>
            </div>

            <div className="performance-chart">
              <h2>실적 추이</h2>
              <div className="chart-container">
                <div className="chart-placeholder">
                  내 실적 차트가 여기에 표시됩니다.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 관리자용 실적 페이지
  return (
    <div className="employee-performance">
      {!showDetailReport ? (
        // 직원 목록 페이지
        <div className="performance-list-page">
          <div className="performance-header">
            <h1>성과 리포트 조회</h1>
          </div>

          <div className="search-section">
            <div className="search-container">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="분석할 직원의 이름 또는 사번을 입력하세요."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          <div className="team-section">
            <h2>나의 팀원</h2>
            <div className="employee-grid">
              {filteredEmployees.map(employee => (
                <div 
                  key={employee.id}
                  className="employee-card-clickable"
                  onClick={() => handleEmployeeClick(employee)}
                >
                  <div className="employee-info">
                    <h4>{employee.name}</h4>
                    <p>{employee.team}</p>
                  </div>
                  <div className="performance-score">
                    {employee.performance}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        // 상세 보고서 페이지
        <div className="detail-report-page">
          <div className="report-header">
            <button className="back-btn" onClick={handleBackToList}>
              ← 목록으로 돌아가기
            </button>
            <h1>직원 성과 보고서</h1>
            <p className="report-subtitle">직원 개발을 위한 상세한 성과 분석 및 전략 인사이트.</p>
          </div>

          <div className="report-content">
            <div className="employee-profile">
              <div className="employee-avatar-large">
                <img src="https://via.placeholder.com/80x80" alt="Employee" />
              </div>
              <div className="employee-info-large">
                <h2>{selectedEmployee.team} {selectedEmployee.name} {selectedEmployee.position}</h2>
                <p>{selectedEmployee.team}</p>
              </div>
            </div>

            <div className="performance-overview-section">
              <h3>성과 개요</h3>
              <div className="performance-cards">
                <div className="performance-card">
                  <h4>할당 업무 완수율</h4>
                  <p className="performance-value">95%</p>
                </div>
                <div className="performance-card">
                  <h4>분기 매출 증감</h4>
                  <p className="performance-value">+12%</p>
                </div>
              </div>
            </div>

            <div className="performance-trend-section">
              <h3>성과 추이</h3>
              <div className="trend-info">
                <p className="trend-value">+8%</p>
                <p className="trend-label">This Quarter +8%</p>
              </div>
              <div className="chart-container">
                <div className="chart-placeholder">
                  성과 추이 차트 (Jan-Jun)
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmployeePerformance; 