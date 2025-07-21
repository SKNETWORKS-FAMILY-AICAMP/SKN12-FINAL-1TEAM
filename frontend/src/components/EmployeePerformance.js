import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './EmployeePerformance.css';

function EmployeePerformance() {
  const navigate = useNavigate();
  const [performanceData, setPerformanceData] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 실적 요약 데이터 가져오기
  const fetchPerformanceSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/employee/performance/summary');
      const data = await response.json();
      
      if (data.success) {
        setPerformanceData(data.summary);
      } else {
        setError(data.message || '실적 데이터를 가져오는데 실패했습니다.');
      }
    } catch (err) {
      setError('서버 연결 오류가 발생했습니다.');
      console.error('실적 요약 조회 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 실적 분석 실행
  const runAnalysis = async (saveReport = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/employee/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employee_name: '최수아',
          period: '202312~202403',
          save_report: saveReport,
          filename: saveReport ? '최수아_실적분석보고서.docx' : null
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setAnalysisData(data);
        if (saveReport) {
          alert('보고서가 성공적으로 생성되었습니다!');
        }
      } else {
        setError(data.message || '분석 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('서버 연결 오류가 발생했습니다.');
      console.error('실적 분석 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 실적 데이터 로드
  useEffect(() => {
    fetchPerformanceSummary();
  }, []);

  return (
    <div className="employee-performance">
      <div className="performance-header">
        <div className="header-left">
          <h1>직원 실적 관리</h1>
        </div>
        <div className="header-center">
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Pharma-Helper</span>
          </div>
        </div>
        <div className="header-right">
          <nav className="header-nav">
            <a href="#" className="nav-link" onClick={(e) => { e.preventDefault(); navigate('/'); }}>홈</a>
            <a href="#" className="nav-link">AI 채팅</a>
            <a href="#" className="nav-link">고객/데이터 위키</a>
            <a href="#" className="nav-link">문서 생성</a>
            <a href="#" className="nav-link active">실적 확인</a>
          </nav>
          <div className="header-actions">
            <button className="notification-btn">🔔</button>
            <div className="user-profile">
              <img src="https://via.placeholder.com/32x32" alt="User" />
            </div>
          </div>
        </div>
      </div>

      <div className="performance-container">
        <div className="performance-sidebar">
          <div className="employee-info">
            <h3>직원 정보</h3>
            <div className="employee-card">
              <div className="employee-avatar">
                <img src="https://via.placeholder.com/80x80" alt="Employee" />
              </div>
              <div className="employee-details">
                <h4>최수아</h4>
                <p>영업팀</p>
                <p>담당 지역: 서부팀</p>
              </div>
            </div>
          </div>
          
          <div className="quick-actions">
            <h3>빠른 작업</h3>
            <button 
              className="action-btn primary" 
              onClick={() => runAnalysis(false)}
              disabled={loading}
            >
              {loading ? '분석 중...' : '실적 분석'}
            </button>
            <button 
              className="action-btn secondary" 
              onClick={() => runAnalysis(true)}
              disabled={loading}
            >
              {loading ? '생성 중...' : '보고서 생성'}
            </button>
            <button 
              className="action-btn refresh" 
              onClick={fetchPerformanceSummary}
              disabled={loading}
            >
              {loading ? '새로고침 중...' : '데이터 새로고침'}
            </button>
          </div>
        </div>

        <div className="performance-main">
          <div className="performance-title">
            <h2>실적 현황</h2>
            <p>2023년 12월 ~ 2024년 3월</p>
          </div>

          {error && (
            <div className="error-message">
              <span>❌ {error}</span>
            </div>
          )}

          {loading && (
            <div className="loading-message">
              <span>⏳ 데이터를 불러오는 중...</span>
            </div>
          )}

          {performanceData && (
            <div className="performance-summary">
              <div className="summary-cards">
                <div className="summary-card">
                  <h3>총 실적</h3>
                  <p className="card-value">
                    {performanceData.total_performance?.toLocaleString() || 0}원
                  </p>
                </div>
                <div className="summary-card">
                  <h3>총 목표</h3>
                  <p className="card-value">
                    {performanceData.total_target?.toLocaleString() || 0}원
                  </p>
                </div>
                <div className="summary-card">
                  <h3>달성률</h3>
                  <p className={`card-value ${performanceData.achievement_rate >= 100 ? 'success' : 'warning'}`}>
                    {performanceData.achievement_rate?.toFixed(1) || 0}%
                  </p>
                </div>
                <div className="summary-card">
                  <h3>상태</h3>
                  <p className={`card-value status-${performanceData.status === '급증' ? 'excellent' : performanceData.status === '안정' ? 'good' : 'poor'}`}>
                    {performanceData.status || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {analysisData && (
            <div className="analysis-results">
              <h3>분석 결과</h3>
              <div className="analysis-content">
                <div className="analysis-section">
                  <h4>기본 정보</h4>
                  <p><strong>직원명:</strong> {analysisData.analysis_result?.employee_name || 'N/A'}</p>
                  <p><strong>기간:</strong> {analysisData.analysis_result?.period || 'N/A'}</p>
                  <p><strong>상태:</strong> {analysisData.analysis_result?.status || 'N/A'}</p>
                </div>
                
                {analysisData.analysis_result?.recommendations && (
                  <div className="analysis-section">
                    <h4>권장사항</h4>
                    <ul>
                      {analysisData.analysis_result.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysisData.report && (
                  <div className="analysis-section">
                    <h4>상세 보고서</h4>
                    <div className="report-preview">
                      {analysisData.report.split('\n').map((line, index) => (
                        <p key={index}>{line}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default EmployeePerformance; 